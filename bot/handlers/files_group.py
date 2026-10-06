import re

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.config import FILES_GROUP_ID
from bot.database import (
    get_order, get_service_order, set_order_status, set_service_order_status,
    list_pending_files, is_admin_user,
)

router = Router()

REF_RE = re.compile(r"REF:(order|service)-(\d+)")
SEND_RE = re.compile(r"(?:(order|service)-)?(\d+)", re.IGNORECASE)


async def _send_record_file(message: Message, bot: Bot, kind: str, record_id: int):
    if kind == "order":
        record = await get_order(record_id)
    else:
        record = await get_service_order(record_id)

    if not record:
        await message.reply("Bunday buyurtma topilmadi.")
        return
    if record["status"] != "tolandi":
        await message.reply("Bu buyurtma to'lovni kutmoqda yoki allaqachon bajarilgan.")
        return

    target_id = record["telegram_id"]
    caption = "✅ Sizning buyurtmangiz tayyor bo'ldi!"
    try:
        if message.document:
            await bot.send_document(target_id, message.document.file_id, caption=caption)
        else:
            await bot.send_photo(target_id, message.photo[-1].file_id, caption=caption)
    except Exception as e:
        await message.reply(f"⚠️ Userga yuborib bo'lmadi: {e}")
        return

    if kind == "order":
        await set_order_status(record_id, "bajarildi")
    else:
        await set_service_order_status(record_id, "bajarildi")
    await message.reply(f"✅ Fayl userga (id: {target_id}) muvaffaqiyatli yuborildi.")


@router.message(Command("pending"), F.chat.id == FILES_GROUP_ID)
async def list_pending(message: Message):
    items = await list_pending_files()
    if not items:
        await message.answer("Hozircha fayl kutayotgan buyurtma yo'q.")
        return
    lines = ["📋 Fayl kutilayotgan buyurtmalar:\n"]
    for it in items:
        ref = f"REF:{it['kind']}-{it['id']}"
        lines.append(f"{ref} — {it['topic']} (USER_ID: {it['telegram_id']})")
    await message.answer("\n".join(lines))


@router.message(F.chat.id == FILES_GROUP_ID, F.reply_to_message, F.document | F.photo)
async def forward_file_by_reply(message: Message, bot: Bot):
    if not message.from_user or not await is_admin_user(message.from_user.id):
        return
    original = message.reply_to_message.text or message.reply_to_message.caption or ""
    match = REF_RE.search(original)
    if not match:
        await message.reply(
            "Bu xabarda buyurtma havolasi (REF:...) topilmadi. Iltimos, "
            "\"Fayl tayyorlanishi kerak\" xabariga to'g'ridan-to'g'ri javob (reply) qiling."
        )
        return

    await _send_record_file(message, bot, match.group(1), int(match.group(2)))


@router.message(Command("send"), F.chat.id == FILES_GROUP_ID, F.document | F.photo)
async def send_file_by_number(message: Message, bot: Bot, command: CommandObject):
    if not message.from_user or not await is_admin_user(message.from_user.id):
        return

    match = SEND_RE.fullmatch((command.args or "").strip())
    if not match:
        await message.reply("Fayl captionida /send 123 yoki /send order-123 yozing.")
        return

    kind, number = match.group(1), int(match.group(2))
    if kind:
        await _send_record_file(message, bot, kind.lower(), number)
        return

    candidates = []
    for candidate_kind, getter in (("order", get_order), ("service", get_service_order)):
        record = await getter(number)
        if record and record["status"] == "tolandi":
            candidates.append(candidate_kind)

    if len(candidates) > 1:
        await message.reply(
            "Bu raqam ikkala turdagi buyurtmada ham bor. Aniq turini kiriting: "
            f"/send order-{number} yoki /send service-{number}."
        )
        return
    if not candidates:
        await message.reply("To'lov qilingan, fayl kutilayotgan buyurtma bu raqam bilan topilmadi.")
        return

    await _send_record_file(message, bot, candidates[0], number)
