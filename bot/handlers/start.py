from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database import get_or_create_user
from bot.database import create_order
from bot.keyboards import admin_order_kb, games_kb, main_menu_kb, other_services_kb, admin_menu_kb
from bot.config import ADMIN_IDS, ADMIN_USERNAME, ORDER_GROUP_ID
from bot.services.payment_common import ask_payment_method
from bot.states import ServiceOrder

router = Router()


SERVICE_OPTIONS = {
    "platforma": [("📱 Mobile", "Mobile"), ("💻 Web-sayt", "Web-sayt"), ("📲 Telegram Web-App", "Telegram Web-App")],
    "biznes hajmi": [("Kichik", "Kichik"), ("O'rta", "O'rta"), ("Katta", "Katta")],
    "dizayn yo'nalishi": [
        ("Minimalizm", "Minimalizm"),
        ("Zamonaviy", "Zamonaviy"),
        ("Hi-Tech", "Hi-Tech"),
        ("3D", "3D"),
        ("Korporativ", "Korporativ"),
    ],
}
OPTIONAL_SERVICE_FIELDS = {
    "qo'shimcha talablar",
    "banner rasmi",
    "rasm (ixtiyoriy)",
    "qo'shimcha ma'lumot",
}


def service_options_kb(field: str):
    builder = InlineKeyboardBuilder()
    for label, value in SERVICE_OPTIONS[field]:
        builder.button(text=label, callback_data=f"svcopt:{value}")
    builder.adjust(2)
    return builder.as_markup()


async def ask_service_field(message: Message, field: str):
    if field in SERVICE_OPTIONS:
        await message.answer(f"{field.capitalize()}ni tanlang:", reply_markup=service_options_kb(field))
    else:
        keyboard = None
        if field in OPTIONAL_SERVICE_FIELDS:
            builder = InlineKeyboardBuilder()
            builder.button(text="⏭ O'tkazib yuborish", callback_data="svcskip")
            keyboard = builder.as_markup()
        await message.answer(f"{field.capitalize()}ni kiriting:", reply_markup=keyboard)


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    text = (
        f"Assalomu alaykum, {message.from_user.full_name}! 👋\n\n"
        "Men — talabalar va ish egalari uchun taqdimot, referat, kurs ishi, "
        "hujjatlar va boshqa xizmatlarni tez va sifatli tayyorlashda yordam beruvchi botman.\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:"
    )
    kb = admin_menu_kb() if user.get("is_admin_mode") else main_menu_kb()
    await message.answer(text, reply_markup=kb)


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    kb = admin_menu_kb() if user.get("is_admin_mode") else main_menu_kb()
    await message.answer("Bosh menyu:", reply_markup=kb)


@router.message(F.text == "🧾 Tadbirkorlar uchun")
async def other_services(message: Message):
    await message.answer(
        "Kerakli xizmatni tanlang. Har bir xizmat bo'yicha quyidagi ma'lumotlar so'raladi: "
        "mavzu, sahifa soni, rasm/grafika/jadvallar, til va boshqa ma'lumotlar. "
        "Tanlagan xizmatingiz bo'yicha to'g'ridan-to'g'ri admin bilan bog'lanasiz.\n\n"
        "Narxlar: Referat — sahifasi 5 000 so'mdan, Mustaqil ish — 8 000 so'mdan, "
        "Kurs ishi — sahifasi 10 000 so'mdan. Boshqa Word ishlari admin bilan kelishiladi. "
        "Agar ish o'zbek tilidan boshqa tilda bo'lsa, sahifa uchun qo'shimcha 1 000 so'm qo'shiladi.",
        reply_markup=other_services_kb(),
    )


@router.message(F.text == "📘 Foydalanish qo'llanmasi")
async def usage_guide(message: Message):
    guide_path = "docs/usage_guide.txt"
    try:
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / guide_path
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        text = (
            "📘 Foydalanish qo'llanmasi\n\n"
            "1. Taqdimotga buyurtma berish bo'limi orqali mavzu, sahifa soni va tarifni tanlang.\n"
            "2. Mustaqil ish, referat, kurs ishi va boshqa Word ishlari uchun alohida buyurtma qoldiring.\n"
            "3. Tadbirkorlar uchun bo'limida xizmat turini tanlab, kerakli ma'lumotlarni kiriting.\n"
            "4. To'lov usulini tanlang: KARTA yoki CLICK. Karta tanlansa, to'lov uchun karta ma'lumotlari ko'rsatiladi; CLICK tanlansa, Click app yoki web-sahifada to'lov talab qilinadi.\n"
            "5. Agar 5 daqiqa ichida to'lov qilinmasa yoki chek yuborilmasa, 5 daqiqalik qo'shimcha vaqt yoki bekor qilish variantlari ko'rsatiladi.\n"
            "6. To'lov tasdiqlangandan keyin fayl tayyorlanadi va kerakli guruhga yuboriladi.\n\n"
            "Narxlar: taqdimot 1 sahifa uchun ko'rsatilgan tarifga ko'ra hisoblanadi. Mustaqil ish va referat narxlari admin tomonidan belgilangan qiymatlarga asoslanadi. "
            "Agar ish o'zbek tilidan boshqa tilda bo'lsa, sahifa uchun qo'shimcha 1 000 so'm hisoblanadi."
        )
        path.write_text(text, encoding="utf-8")
        from aiogram.types import FSInputFile
        await message.answer_document(FSInputFile(path, filename="usage_guide.txt"))
    except Exception:
        await message.answer(
            "📘 Foydalanish qo'llanmasi\n\n"
            "1. Taqdimotga buyurtma berish bo'limi orqali mavzu, sahifa soni va tarifni tanlang.\n"
            "2. Mustaqil ish, referat, kurs ishi va boshqa Word ishlari uchun alohida buyurtma qoldiring.\n"
            "3. Tadbirkorlar uchun bo'limida xizmat turini tanlab, kerakli ma'lumotlarni kiriting.\n"
            "4. To'lov usulini tanlang: KARTA yoki CLICK.\n"
            "5. Agar 5 daqiqa ichida to'lov qilinmasa yoki chek yuborilmasa, 5 daqiqalik qo'shimcha vaqt yoki bekor qilish variantlari ko'rsatiladi."
        )


@router.callback_query(F.data.startswith("other_service:"))
async def other_service_chosen(callback: CallbackQuery, state: FSMContext, bot: Bot):
    service = callback.data.split(":", 1)[1]
    fields = {
        "Taklifnoma": ["to'y kuni", "kelin-kuyov ismlari", "familiya/oila nomi", "to'yxona manzili", "qo'shimcha talablar"],
        "UI dizayn": ["platforma", "biznes turi", "biznes hajmi", "dizayn yo'nalishi", "qo'shimcha talablar"],
        "Web-sayt": ["tadbirkorlik turi", "sayt mavzusi", "dizayn yo'nalishi", "qo'shimcha talablar"],
        "Rezyume": ["F.I.Sh.", "telefon va email", "ta'lim", "ish tajribasi", "ko'nikmalar va tillar", "qo'shimcha ma'lumot"],
        "YouTube banner": ["kanal nomi", "bannerda bo'ladigan matn va ijtimoiy tarmoqlar", "banner rasmi", "qo'shimcha talablar"],
        "Logo": ["logo nomi", "ranglar", "rasm (ixtiyoriy)", "biznes yo'nalishi", "biznes haqida qisqacha ma'lumot"],
        "QR-generator": ["QR kodga aylantiriladigan link"],
    }
    prompts = fields.get(service, ["buyurtma tafsilotlari"])
    await state.set_state(ServiceOrder.waiting_topic)
    await state.update_data(service_name=service, fields=prompts, field_index=0, answers={})
    await ask_service_field(callback.message, prompts[0])
    await callback.answer()


@router.message(ServiceOrder.waiting_topic)
async def service_order_topic(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    if message.text in {"🎮 O'yin va ko'ngil ochish", "ℹ️ Biz haqimizda", "ℹ️ Admin bilan bog'lanish"}:
        await state.clear()
        if message.text == "🎮 O'yin va ko'ngil ochish":
            await message.answer("O'yin va ko'ngil ochish:", reply_markup=games_kb())
        elif message.text == "ℹ️ Biz haqimizda":
            await about_us(message)
        else:
            await contact_admin(message)
        return
    answers = dict(data.get("answers") or {})
    fields = data.get("fields") or []
    index = int(data.get("field_index", 0))
    answers[fields[index]] = (message.text or "").strip() or "-"
    index += 1
    if index < len(fields):
        await state.update_data(answers=answers, field_index=index)
        await ask_service_field(message, fields[index])
        return
    service = data.get("service_name", "Boshqa xizmat")
    price = {
        "Taklifnoma": 50_000,
        "UI dizayn": 500_000,
        "Web-sayt": 1_000_000,
        "Rezyume": 50_000,
        "YouTube banner": 50_000,
        "Logo": 100_000,
        "QR-generator": 30_000,
    }.get(service, "Admin bilan kelishiladi")
    price_label = f"{price:,} so'm".replace(",", ".") if isinstance(price, int) else price
    summary = (
        f"🧾 Yangi xizmat buyurtmasi\n"
        f"Xizmat: {service}\n"
        f"Boshlang'ich narx: {price_label}\n"
        + "\n".join(f"{key}: {value}" for key, value in answers.items())
        + "\n\n"
        f"Foydalanuvchi: @{message.from_user.username or 'unknown'} (id: {message.from_user.id})"
    )
    if isinstance(price, int):
        order_id = await create_order({
            "telegram_id": message.from_user.id,
            "topic": service,
            "pages": 1,
            "tariff": service,
            "price_som": price,
            "price_mpt": 0,
            "full_name": message.from_user.full_name,
            "institution": summary,
            "direction": "",
            "language": "",
        })
        await bot.send_message(
            ORDER_GROUP_ID,
            f"{summary}\nBuyurtma №{order_id}\nHolat: To'lov kutilmoqda",
            reply_markup=admin_order_kb(order_id),
        )
        await ask_payment_method(message, state, "order", price, str(order_id))
    else:
        await state.clear()
        await bot.send_message(ORDER_GROUP_ID, summary)
        await message.answer(
            "✅ Buyurtmangiz adminlarga yuborildi. Narx admin bilan kelishiladi.",
            reply_markup=main_menu_kb(),
        )


@router.callback_query(ServiceOrder.waiting_topic, F.data.startswith("svcopt:"))
async def service_option_selected(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    answers = dict(data.get("answers") or {})
    fields = data.get("fields") or []
    index = int(data.get("field_index", 0))
    value = callback.data.split(":", 1)[1]
    answers[fields[index]] = value
    index += 1
    if index < len(fields):
        await state.update_data(answers=answers, field_index=index)
        await ask_service_field(callback.message, fields[index])
    else:
        await state.update_data(answers=answers, field_index=index)
        await callback.message.answer("Oxirgi ma'lumot qabul qilindi. Buyurtma yuborildi.")
    await callback.answer()


@router.callback_query(ServiceOrder.waiting_topic, F.data == "svcskip")
async def service_optional_skipped(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    answers = dict(data.get("answers") or {})
    fields = data.get("fields") or []
    index = int(data.get("field_index", 0))
    answers[fields[index]] = "O'tkazib yuborildi"
    index += 1
    await state.update_data(answers=answers, field_index=index)
    if index < len(fields):
        await ask_service_field(callback.message, fields[index])
    else:
        service = data.get("service_name", "Boshqa xizmat")
        price = {
            "Taklifnoma": 50_000, "UI dizayn": 500_000, "Web-sayt": 1_000_000,
            "Rezyume": 50_000, "YouTube banner": 50_000, "Logo": 100_000,
            "QR-generator": 30_000,
        }.get(service, 0)
        summary = (
            f"🧾 Yangi xizmat buyurtmasi\nXizmat: {service}\n"
            f"Boshlang'ich narx: {price:,} so'm\n"
            + "\n".join(f"{key}: {value}" for key, value in answers.items())
            + f"\n\nFoydalanuvchi: @{callback.from_user.username or 'unknown'} "
              f"(id: {callback.from_user.id})"
        )
        if price:
            order_id = await create_order({
                "telegram_id": callback.from_user.id, "topic": service, "pages": 1,
                "tariff": service, "price_som": price, "price_mpt": 0,
                "full_name": callback.from_user.full_name, "institution": summary,
                "direction": "", "language": "",
            })
            await callback.bot.send_message(
                ORDER_GROUP_ID, f"{summary}\nBuyurtma №{order_id}\nHolat: To'lov kutilmoqda",
                reply_markup=admin_order_kb(order_id),
            )
            await ask_payment_method(callback.message, state, "order", price, str(order_id))
        else:
            await callback.bot.send_message(ORDER_GROUP_ID, summary)
            await state.clear()
            await callback.message.answer("✅ Buyurtmangiz yuborildi.", reply_markup=main_menu_kb())
    await callback.answer()


@router.message(F.text == "🎮 O'yin va ko'ngil ochish")
async def games_menu_from_any_state(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "O'yin va ko'ngil ochish:",
        reply_markup=games_kb(),
    )


@router.message(F.text == "ℹ️ Biz haqimizda")
async def about_us_from_any_state(message: Message, state: FSMContext):
    await state.clear()
    await about_us(message)


@router.message(F.text == "ℹ️ Admin bilan bog'lanish")
async def contact_admin_from_any_state(message: Message, state: FSMContext):
    await state.clear()
    await contact_admin(message)


@router.message(F.text == "ℹ️ Admin bilan bog'lanish")
async def contact_admin(message: Message):
    await message.answer(
        "Bot asoschisi va PreUz bosh direktori: https://t.me/MUKHAMMADSODlQ\n"
        "Ikkinchi akkaunt: https://t.me/MUHAMMADS0DlQ\n"
        "Adminlar: https://t.me/preuzadmin\n"
        "Admin1: https://t.me/preuzadmin\n"
        "Admin2: https://t.me/MUKHAMMADSODlQ",
        disable_web_page_preview=False,
    )


@router.message(F.text == "🎮 O'yin va ko'ngil ochish")
async def games_menu(message: Message):
    # Menyu tugmasi oldingi buyurtma FSM holatini bekor qiladi.
    from aiogram.fsm.context import FSMContext
    await message.answer(
        "O'yin va ko'ngil ochish uchun quyidagi havolalardan birini tanlang:",
        reply_markup=games_kb(),
    )


@router.message(F.text == "ℹ️ Biz haqimizda")
async def about_us(message: Message):
    text = (
        "Biz “PreUz” jamoasi 5+ yildan buyon nafaqat O‘zbekiston balki, MDH mamlakatlari talabalariga ham xizmat ko‘rsatib kelmoqdamiz. "
        "Bu bot hozircha siz uchun taqdimot tayyorlamaydi. U shunchaki sizdan kerakli ma'lumotlarni oladi va adminlarga yuboradi. "
        "Va biz siz taqdim etgan ma'lumotlar asosida xizmatlarni taqdim etamiz. Bizning barcha xizmatlarimiz faqat elektron shaklda taqdim etiladi, "
        "biz qo'l yozuvi, chizmachilik yoki chop etish bilan shug'ullanmaymiz. Agar siz botni tushunishda muammolarga duch kelsangiz yoki narxlar bilan bog'liq muammolarga duch kelsangiz, "
        "\"To'g'ridan-to'g'ri administratorlarga buyurtma berish\" tugmasi orqali administratorlardan buyurtma bering!\n\n"
        "Bot asoschisi va PreUz bosh direktori: https://t.me/MUKHAMMADSODlQ\n"
        "Ikkinchi akkaunt: https://t.me/MUHAMMADS0DlQ\n"
        "Kanal: https://t.me/preuzb\n"
        "Ishonch kanali: https://t.me/pre_ishonch\n"
        "Adminlar: https://t.me/preuzadmin, https://t.me/MUKHAMMADSODlQ\n"
        "'Soff'dagi biz: https://soff.uz/seller/879\n"
        "Instagram: https://www.instagram.com/mukhammadsodlq?igsh=MWR4dHRzc3ZjYnV2dw==\n"
        "Donat uchun: https://tirikchilik.uz/mukhammadsodiq\n\n"
        "Aloqa raqamlari:\n+998996665732\n+998901995732\n+998942881488"
    )
    await message.answer(text, disable_web_page_preview=False)


@router.message(F.text == "🤖 Sun'iy intellekt yordamida")
async def ai_menu(message: Message):
    await message.answer(
        "Bu bo'lim hozircha ishlab chiqilmoqda. Tez orada AI yordamida "
        "taqdimot, referat va mustaqil ish generatsiyasi qo'shiladi."
    )
