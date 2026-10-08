import asyncio
import html
import logging
import os
import re
import tempfile

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import FILES_GROUP_ID
from bot.database import (
    create_manual_presentation,
    get_manual_presentation,
    get_user,
    is_admin_user,
    list_admin_ids,
    set_manual_presentation_status,
)
from bot.i18n import normalize_language, tr
from bot.keyboards import manual_photo_kb, manual_review_kb
from bot.services.pptx_generator import build_manual_presentation, pick_random_template
from bot.states import ManualPresentation

router = Router()
logger = logging.getLogger(__name__)
ALLOWED_TEMPLATES = ("1.pptx", "2.pptx", "3.pptx")
MAX_TEXT_FILE_BYTES = 256_000


def _paragraphs_from_text(text: str, expected: int) -> list[str] | None:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", normalized) if part.strip()]
    if len(paragraphs) != expected:
        lines = [line.strip() for line in normalized.splitlines() if line.strip()]
        if len(lines) == expected:
            paragraphs = lines
    return paragraphs if len(paragraphs) == expected else None


def image_limit_for_pages(pages: int) -> int:
    return min(pages, max(0, pages - 4))


async def begin_manual_presentation(callback: CallbackQuery, state: FSMContext, data: dict):
    from bot.database import get_user

    user = await get_user(callback.from_user.id)
    ui_language = normalize_language(user.get("lang") if user else None)
    await state.update_data(manual_ui_language=ui_language)
    await state.set_state(ManualPresentation.waiting_essay)
    await callback.message.answer(tr(ui_language, "manual_prompt_intro"))
    prompt = tr(
        ui_language,
        "manual_prompt",
        topic=data["topic"],
        pages=data["pages"],
        language=data.get("language") or "O'zbek",
    )
    await callback.message.answer(f"<pre>{html.escape(prompt)}</pre>", parse_mode="HTML")
    await callback.message.answer(
        tr(ui_language, "manual_text_request", pages=data["pages"]),
    )


async def _receive_essay(message: Message, state: FSMContext, bot: Bot, text: str):
    data = await state.get_data()
    language = normalize_language(data.get("manual_ui_language"))
    paragraphs = _paragraphs_from_text(text, data["pages"])
    if not paragraphs:
        await message.answer(
            tr(language, "manual_text_invalid", pages=data["pages"]),
        )
        return

    await state.update_data(manual_paragraphs=paragraphs, manual_image_file_ids=[])
    image_limit = image_limit_for_pages(data["pages"])
    if not image_limit:
        await _generate_and_send_for_review(message, state, bot)
        return

    await state.set_state(ManualPresentation.waiting_photos)
    await message.answer(
        tr(language, "manual_photos_intro", count=image_limit),
        reply_markup=manual_photo_kb(language),
    )


@router.message(ManualPresentation.waiting_essay, F.text)
async def receive_manual_essay(message: Message, state: FSMContext, bot: Bot):
    await _receive_essay(message, state, bot, message.text or "")


@router.message(ManualPresentation.waiting_essay, F.document)
async def receive_manual_essay_file(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    language = normalize_language(data.get("manual_ui_language"))
    document = message.document
    if not document.file_name or not document.file_name.lower().endswith(".txt"):
        await message.answer(tr(language, "manual_txt_only"))
        return
    if document.file_size and document.file_size > MAX_TEXT_FILE_BYTES:
        await message.answer(tr(language, "manual_txt_large"))
        return
    downloaded = await bot.download(document.file_id)
    if downloaded is None:
        raise RuntimeError("Telegram returned no content for the presentation text file.")
    try:
        text = downloaded.getvalue().decode("utf-8-sig")
    except UnicodeDecodeError:
        await message.answer(tr(language, "manual_txt_encoding"))
        return
    await _receive_essay(message, state, bot, text)


@router.message(ManualPresentation.waiting_photos, F.photo)
async def receive_manual_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    language = normalize_language(data.get("manual_ui_language"))
    image_limit = image_limit_for_pages(data["pages"])
    image_file_ids = data.get("manual_image_file_ids", [])
    if len(image_file_ids) >= image_limit:
        await message.answer(tr(language, "manual_photo_limit"))
        return
    image_file_ids.append(message.photo[-1].file_id)
    await state.update_data(manual_image_file_ids=image_file_ids)
    await message.answer(
        tr(
            language,
            "manual_photo_added",
            received=len(image_file_ids),
            count=image_limit,
        ),
    )


@router.message(ManualPresentation.waiting_photos)
async def reject_non_photo_in_photo_step(message: Message, state: FSMContext):
    data = await state.get_data()
    language = normalize_language(data.get("manual_ui_language"))
    await message.answer(
        tr(language, "manual_photos_intro", count=image_limit_for_pages(data["pages"])),
        reply_markup=manual_photo_kb(language),
    )


@router.callback_query(
    ManualPresentation.waiting_photos,
    F.data.in_({"manual:finish_photos", "manual:skip_photos"}),
)
async def finish_manual_photos(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    language = normalize_language(data.get("manual_ui_language"))
    key = "manual_no_photos" if callback.data.endswith("skip_photos") else "manual_generating"
    await callback.answer()
    await callback.message.answer(tr(language, key))
    await _generate_and_send_for_review(callback.message, state, bot)


async def _generate_and_send_for_review(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    language = normalize_language(data.get("manual_ui_language"))
    template_path = pick_random_template("bepul", allowed_files=ALLOWED_TEMPLATES)
    if not template_path:
        await state.clear()
        await message.answer(tr(language, "manual_failed"))
        logger.error("No allowed free PowerPoint template was found.")
        return

    presentation_id = None
    temp_paths: list[str] = []
    try:
        presentation_id = await create_manual_presentation({
            "telegram_id": message.chat.id,
            "topic": data["topic"],
            "pages": data["pages"],
            "full_name": data.get("full_name") or "",
            "institution": data.get("institution") or "",
            "direction": data.get("direction") or "",
            "language": data.get("language") or "O'zbek",
            "paragraphs": data["manual_paragraphs"],
            "image_file_ids": data.get("manual_image_file_ids", []),
            "template_name": os.path.basename(template_path),
        })
        await message.answer(tr(language, "manual_generating"))

        image_paths = []
        for file_id in data.get("manual_image_file_ids", []):
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as image_file:
                image_path = image_file.name
            temp_paths.append(image_path)
            downloaded = await bot.download(file_id, destination=image_path)
            if downloaded is None:
                raise RuntimeError("Telegram returned no image data for the presentation.")
            image_paths.append(image_path)

        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as output:
            output_path = output.name
        temp_paths.append(output_path)
        await asyncio.to_thread(
            build_manual_presentation,
            template_path=template_path,
            output_path=output_path,
            topic=data["topic"],
            full_name=data.get("full_name") or "",
            institution=data.get("institution") or "",
            direction=data.get("direction") or "",
            paragraphs=data["manual_paragraphs"],
            image_paths=image_paths,
        )
        document = await bot.send_document(
            FILES_GROUP_ID,
            FSInputFile(output_path, filename=f"PreUz_presentation_{presentation_id}.pptx"),
            caption=tr(
                "uz",
                "manual_admin_caption",
                id=presentation_id,
                user_id=message.chat.id,
                topic=data["topic"],
            ),
        )
        if not document.document:
            raise RuntimeError("Telegram did not return a document for admin review.")
        if not await set_manual_presentation_status(
            presentation_id,
            "generating",
            "awaiting_approval",
            document_file_id=document.document.file_id,
        ):
            raise RuntimeError(f"Manual presentation state changed during generation (id={presentation_id}).")
        review_text = tr("uz", "manual_review_prompt", id=presentation_id)
        try:
            await bot.send_message(
                FILES_GROUP_ID,
                review_text,
                reply_markup=manual_review_kb(presentation_id),
            )
        except TelegramAPIError:
            logger.exception(
                "Manual presentation review controls could not be sent to the files group "
                "(presentation_id=%s)",
                presentation_id,
            )
            delivered_to_admin = False
            for admin_id in await list_admin_ids():
                if not admin_id:
                    continue
                try:
                    await bot.send_message(
                        admin_id,
                        review_text,
                        reply_markup=manual_review_kb(presentation_id),
                    )
                    delivered_to_admin = True
                except TelegramAPIError:
                    logger.exception(
                        "Manual presentation review controls could not be sent to admin "
                        "(presentation_id=%s admin_id=%s)",
                        presentation_id,
                        admin_id,
                    )
            if not delivered_to_admin:
                raise RuntimeError("Could not deliver manual presentation review controls to any admin.")

        await message.answer(tr(language, "manual_submitted"))
        await state.clear()
    except Exception:
        if presentation_id is not None:
            for expected_status in ("generating", "awaiting_approval"):
                if await set_manual_presentation_status(
                    presentation_id, expected_status, "failed",
                ):
                    break
        logger.exception(
            "Manual presentation generation or admin handoff failed (presentation_id=%s user_id=%s)",
            presentation_id,
            message.chat.id,
        )
        await message.answer(tr(language, "manual_failed"))
        await state.clear()
    finally:
        for path in temp_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    logger.exception("Temporary presentation file could not be removed (path=%s)", path)


@router.callback_query(F.data.startswith("manual:approve:"))
async def approve_manual_presentation(callback: CallbackQuery, bot: Bot):
    presentation_id = int(callback.data.rsplit(":", 1)[1])
    if not await is_admin_user(callback.from_user.id):
        await callback.answer(tr("uz", "manual_admin_only"), show_alert=True)
        return

    presentation = await get_manual_presentation(presentation_id)
    if (
        not presentation
        or presentation["status"] != "awaiting_approval"
        or not presentation["document_file_id"]
    ):
        await callback.answer(tr("uz", "manual_already_reviewed"), show_alert=True)
        return
    if not await set_manual_presentation_status(
        presentation_id, "awaiting_approval", "delivering",
    ):
        await callback.answer(tr("uz", "manual_already_reviewed"), show_alert=True)
        return

    try:
        user = await get_user(presentation["telegram_id"])
        await bot.send_document(
            presentation["telegram_id"],
            presentation["document_file_id"],
            caption=tr(
                user.get("lang") if user else None,
                "manual_approved_user",
            ),
        )
    except Exception:
        await set_manual_presentation_status(
            presentation_id, "delivering", "awaiting_approval",
        )
        logger.exception(
            "Approved manual presentation could not be delivered (presentation_id=%s user_id=%s)",
            presentation_id,
            presentation["telegram_id"],
        )
        await callback.answer("Fayl foydalanuvchiga yuborilmadi. Qayta urinib ko'ring.", show_alert=True)
        return

    await set_manual_presentation_status(presentation_id, "delivering", "delivered")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramAPIError:
        logger.exception("Could not remove review buttons (presentation_id=%s)", presentation_id)
    await callback.answer(tr("uz", "manual_approved_admin"))


@router.callback_query(F.data.startswith("manual:reject:"))
async def reject_manual_presentation(callback: CallbackQuery, bot: Bot):
    presentation_id = int(callback.data.rsplit(":", 1)[1])
    if not await is_admin_user(callback.from_user.id):
        await callback.answer(tr("uz", "manual_admin_only"), show_alert=True)
        return

    presentation = await get_manual_presentation(presentation_id)
    if not presentation or not await set_manual_presentation_status(
        presentation_id, "awaiting_approval", "rejected",
    ):
        await callback.answer(tr("uz", "manual_already_reviewed"), show_alert=True)
        return
    try:
        user = await get_user(presentation["telegram_id"])
        await bot.send_message(
            presentation["telegram_id"],
            tr(user.get("lang") if user else None, "manual_rejected_user"),
        )
    except TelegramAPIError:
        logger.exception(
            "Rejected manual presentation notification could not be delivered "
            "(presentation_id=%s user_id=%s)",
            presentation_id,
            presentation["telegram_id"],
        )
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramAPIError:
        logger.exception("Could not remove review buttons (presentation_id=%s)", presentation_id)
    await callback.answer(tr("uz", "manual_rejected_admin"))
