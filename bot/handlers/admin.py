import datetime
import asyncio
import re

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.config import ADMIN_IDS, SUBSCRIPTIONS, OWNER_ID, FILES_GROUP_ID
from bot.states import AdminBroadcast
from bot.keyboards import admin_menu_kb, main_menu_kb
from bot.database import (
    add_mpt_balance, get_user, set_order_status, get_order,
    list_pending_orders, set_subscription, set_admin_mode,
    list_all_users, get_total_paid_revenue, get_or_create_user,
    get_order_for_delivery,
)

router = Router()


@router.message(F.chat.id == FILES_GROUP_ID, F.document)
async def deliver_ready_file(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    caption = message.caption or ""
    match = re.search(r"(?:№|order[_ -]?id[: ]*|USER_ID[: ]*)(\d+)", caption, re.IGNORECASE)
    if not match:
        await message.reply("Faylni yuborishda captionga buyurtma raqamini yozing: №123")
        return
    order = await get_order_for_delivery(match.group(1))
    if not order:
        await message.reply("Bu raqamga mos buyurtma topilmadi.")
        return
    await bot.send_document(
        order["telegram_id"],
        message.document.file_id,
        caption=f"✅ №{order['id']} buyurtmangiz tayyor. Fayl yuborildi.",
    )
    await set_order_status(order["id"], "fayl_yuborildi")
    await message.reply(f"✅ №{order['id']} fayli userga yuborildi.")


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS or user_id == OWNER_ID


@router.message(Command("admin"))
async def toggle_admin_mode(message: Message):
    """FAQAT bot egasi (OWNER_ID) uchun ishlaydi. Boshqa hech kim bu buyruq
    orqali hech narsaga erisha olmaydi va admin rejasi haqida bilib qolmaydi."""
    if message.from_user.id != OWNER_ID:
        return  # boshqalar uchun bu buyruq sezilmasligi kerak - hech qanday javob yo'q
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    new_mode = not bool(user.get("is_admin_mode"))
    await set_admin_mode(message.from_user.id, new_mode)
    if new_mode:
        await message.answer("🛠 Admin rejasi yoqildi.", reply_markup=admin_menu_kb())
    else:
        await message.answer("👤 Oddiy foydalanuvchi rejasiga qaytdingiz.", reply_markup=main_menu_kb())


@router.message(Command("groupid"))
async def cmd_groupid(message: Message):
    """Guruh/kanal ID sini bilish uchun: botni o'sha guruhga qo'shib, shu buyruqni yuboring.
    Chiqqan ID ni .env faylidagi PAYMENT_GROUP_ID ga yozing."""
    if message.from_user.id != OWNER_ID:
        return
    await message.answer(f"Ushbu chat ID: <code>{message.chat.id}</code>", parse_mode="HTML")


@router.message(F.text == "📊 Statistika")
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    users = await list_all_users()
    revenue = await get_total_paid_revenue()
    text = (
        f"👥 Jami foydalanuvchilar: {len(users)}\n\n"
        f"💳 Click orqali to'lovlar: {revenue['click_count']} ta, jami {revenue['click_total']:,.0f} so'm\n"
        f"🏦 Karta orqali to'lovlar: {revenue['card_count']} ta, jami {revenue['card_total']:,.0f} so'm\n\n"
        "<i>Diqqat: bu — bot orqali qayd etilgan va tasdiqlangan to'lovlar yig'indisi, "
        "haqiqiy bank/karta balansi emas. Aniq balansni bank ilovangizdan tekshiring.</i>"
    ).replace(",", ".")
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🛍 Soff.uz'ga yuklash")
async def admin_soff_upload(message: Message):
    if not is_admin(message.from_user.id):
        return
    from bot.config import SOFF_SELLER_PANEL_URL
    await message.answer(
        "Yangi mahsulot yuklash uchun sotuvchi panelingizga o'ting:\n"
        f"{SOFF_SELLER_PANEL_URL}\n\n"
        "<i>Eslatma: hozircha yuklashni avtomatlashtirish uchun soff.uz'ning yuklash "
        "API'siga (yoki avtorizatsiya usuliga) kirish kerak. Agar shu haqda "
        "ma'lumot (masalan, seller panelidagi \"Network\" so'rovlari yoki API hujjat) "
        "bersangiz, buni ham botga ulab beraman.</i>",
        parse_mode="HTML",
    )


@router.message(F.text == "👤 Foydalanuvchiga xabar")
async def admin_msg_one_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminBroadcast.waiting_target_id)
    await message.answer("Foydalanuvchining Telegram ID raqamini kiriting:")


@router.message(AdminBroadcast.waiting_target_id)
async def admin_msg_one_get_id(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, faqat raqam (Telegram ID) kiriting.")
        return
    await state.update_data(target_id=int(message.text.strip()))
    await state.set_state(AdminBroadcast.waiting_single_message)
    await message.answer("Endi yuboriladigan xabar matnini kiriting:")


@router.message(AdminBroadcast.waiting_single_message)
async def admin_msg_one_send(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    try:
        await bot.send_message(data["target_id"], message.text)
        await message.answer("✅ Xabar yuborildi.", reply_markup=admin_menu_kb())
    except Exception as e:
        await message.answer(f"⚠️ Xabar yuborilmadi: {e}", reply_markup=admin_menu_kb())
    await state.clear()


@router.message(F.text == "📢 Barchaga xabar")
async def admin_broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminBroadcast.waiting_broadcast_message)
    await message.answer("Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:")


@router.message(AdminBroadcast.waiting_broadcast_message)
async def admin_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    users = await list_all_users()
    await message.answer(f"Yuborish boshlandi ({len(users)} foydalanuvchiga)...")
    sent, failed = 0, 0
    for user in users:
        try:
            await bot.send_message(user["telegram_id"], message.text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # Telegram flood-limitiga tushmaslik uchun
    await message.answer(f"✅ Yuborildi: {sent} ta, xato: {failed} ta.", reply_markup=admin_menu_kb())
    await state.clear()


@router.message(F.text == "🔙 Oddiy rejimga qaytish")
async def back_to_user_mode(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    await set_admin_mode(message.from_user.id, False)
    await message.answer("👤 Oddiy foydalanuvchi rejasiga qaytdingiz.", reply_markup=main_menu_kb())


@router.message(Command("addmpt"))
async def cmd_addmpt(message: Message):
    """/addmpt <telegram_id> <miqdor> — foydalanuvchi balansiga MPT qo'shish (admin uchun, to'lov qabul qilingach)."""
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Foydalanish: /addmpt <telegram_id> <miqdor>")
        return
    try:
        telegram_id = int(parts[1])
        amount = float(parts[2])
    except ValueError:
        await message.answer("Noto'g'ri format. Masalan: /addmpt 123456789 50")
        return
    await add_mpt_balance(telegram_id, amount)
    user = await get_user(telegram_id)
    await message.answer(f"✅ {telegram_id} foydalanuvchiga {amount} MPT qo'shildi. Yangi balans: {user['mpt_balance']:.1f} MPT")


@router.message(Command("addsub"))
async def cmd_addsub(message: Message):
    """/addsub <telegram_id> <tarif_kaliti> — foydalanuvchiga obuna faollashtirish."""
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 3 or parts[2] not in SUBSCRIPTIONS:
        keys = ", ".join(SUBSCRIPTIONS.keys())
        await message.answer(f"Foydalanish: /addsub <telegram_id> <{keys}>")
        return
    telegram_id = int(parts[1])
    sub = SUBSCRIPTIONS[parts[2]]
    expiry = (datetime.datetime.utcnow() + datetime.timedelta(days=sub["days"])).isoformat()
    await set_subscription(telegram_id, parts[2], expiry)
    await message.answer(f"✅ {telegram_id} uchun “{sub['title']}” obunasi {expiry[:10]} sanagacha faollashtirildi.")


@router.message(F.text == "🧾 Kutayotgan buyurtmalar")
async def admin_orders_button(message: Message):
    if not is_admin(message.from_user.id):
        return
    await cmd_orders(message)


@router.message(Command("orders"))
async def cmd_orders(message: Message):
    if not is_admin(message.from_user.id):
        return
    orders = await list_pending_orders()
    if not orders:
        await message.answer("Kutilayotgan buyurtmalar yo'q.")
        return
    lines = [f"№{o['id']} | {o['topic']} | {o['pages']} sahifa | {o['tariff']} | {o['status']}" for o in orders]
    await message.answer("\n".join(lines))


@router.callback_query(F.data.startswith("admin_done:"))
async def admin_mark_done(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    order_id = int(callback.data.split(":", 1)[1])
    await set_order_status(order_id, "bajarildi")
    order = await get_order(order_id)
    await callback.message.answer(f"✅ Buyurtma №{order_id} bajarildi deb belgilandi.")
    if not order:
        await callback.answer()
        return

    # Shablon topilsa - avtomatik generatsiya qilib, to'g'ridan-to'g'ri userga yuboramiz.
    # Shablon topilmasa (hali yuklamagan bo'lsangiz) - eski xatti-harakat: shunchaki xabar.
    from bot.services.pptx_generator import pick_random_template, build_presentation
    template_path = pick_random_template(order["tariff"])
    if template_path:
        try:
            output_path = f"/tmp/order_{order_id}.pptx"
            build_presentation(
                template_path=template_path,
                output_path=output_path,
                topic=order["topic"],
                full_name=order["full_name"],
                institution=order["institution"] or "",
                direction=order["direction"] or "",
                total_pages=order["pages"],
            )
            from aiogram.types import FSInputFile
            await bot.send_document(order["telegram_id"], FSInputFile(output_path), caption="✅ Taqdimotingiz tayyor!")
        except Exception as e:
            await callback.message.answer(f"⚠️ Avtomatik generatsiyada xatolik: {e}. Faylni qo'lda yuboring.")
            await bot.send_message(order["telegram_id"], f"✅ Sizning №{order_id} buyurtmangiz tayyor! Fayl tez orada yuboriladi.")
    else:
        await bot.send_message(
            order["telegram_id"],
            f"✅ Sizning №{order_id} buyurtmangiz tayyor! Fayl tez orada yuboriladi."
        )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_reject:"))
async def admin_reject(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    order_id = int(callback.data.split(":", 1)[1])
    await set_order_status(order_id, "rad etildi")
    order = await get_order(order_id)
    await callback.message.answer(f"❌ Buyurtma №{order_id} rad etildi.")
    if order:
        await bot.send_message(
            order["telegram_id"],
            f"❌ Sizning №{order_id} buyurtmangiz rad etildi. Batafsil uchun admin bilan bog'laning."
        )
    await callback.answer()
