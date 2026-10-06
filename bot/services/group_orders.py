import datetime

from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import ORDERS_GROUP_ID

PENDING_MARK = "⏳ Jarayonda..."
ACCEPTED_MARK = "✅ Qabul qilindi."
CANCELLED_MARK = "❌ Bekor qilindi."
# Uzbekistan uses UTC+05:00 year-round.
TASHKENT_TIMEZONE = datetime.timezone(datetime.timedelta(hours=5))


def tashkent_timestamp() -> str:
    return datetime.datetime.now(TASHKENT_TIMEZONE).strftime("%d.%m.%Y %H:%M")


def confirm1_kb():
    b = InlineKeyboardBuilder()
    b.button(text="✅ Tasdiqlayman", callback_data="flow_confirm")
    b.button(text="❌ Bekor qilish", callback_data="flow_cancel")
    b.adjust(2)
    return b.as_markup()


def confirm2_kb():
    b = InlineKeyboardBuilder()
    b.button(text="✅ Ha, ishonchim komil", callback_data="flow_confirm")
    b.button(text="❌ Yo'q, bekor qilaman", callback_data="flow_cancel")
    b.adjust(2)
    return b.as_markup()


async def post_pending_group_message(bot: Bot, lines: list[str]) -> tuple[int, str]:
    """Buyurtma haqidagi dastlabki ma'lumotni "Buyurtmalarim" guruhiga yuboradi,
    oxiriga "Jarayonda..." belgisini qo'shadi. (message_id, to'liq_matn) qaytaradi."""
    full_text = "\n".join(lines) + f"\n\n{PENDING_MARK}"
    msg = await bot.send_message(ORDERS_GROUP_ID, full_text)
    return msg.message_id, full_text


async def mark_group_message(bot: Bot, message_id: int, previous_text: str, new_mark: str):
    """Guruhdagi xabarni tahrirlab, "Jarayonda..."ni boshqa holat bilan almashtiradi."""
    new_text = previous_text.replace(PENDING_MARK, new_mark)
    try:
        await bot.edit_message_text(chat_id=ORDERS_GROUP_ID, message_id=message_id, text=new_text)
    except Exception:
        pass
    return new_text


async def attach_keyboard(bot: Bot, message_id: int, kb):
    try:
        await bot.edit_message_reply_markup(chat_id=ORDERS_GROUP_ID, message_id=message_id, reply_markup=kb)
    except Exception:
        pass


async def begin_confirmation(message, state, **data):
    """Barcha ma'lumot yig'ib bo'lingach shu funksiya chaqiriladi: state'ga
    ma'lumotlarni yozadi va birinchi tasdiqlash bosqichini boshlaydi.
    Majburiy kalitlar: flow_kind ('presentation' yoki 'service'), telegram_id,
    topic, group_lines (list[str]), price_som (yoki None), va flow_kind='service'
    bo'lsa service_type, summary_text."""
    from bot.states import OrderConfirm
    preview_text = data.pop("preview_text", "Ma'lumotlaringizni tasdiqlaysizmi?")
    await state.update_data(**data)
    await state.set_state(OrderConfirm.confirm1)
    await message.answer(preview_text, parse_mode="HTML", reply_markup=confirm1_kb())
