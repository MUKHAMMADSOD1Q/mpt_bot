from bot.database import get_user
from bot.i18n import normalize_language
from bot.keyboards import main_menu_kb


async def get_user_locale(telegram_id: int) -> str:
    user = await get_user(telegram_id)
    return normalize_language(user.get("lang") if user else None)


async def localized_main_menu(telegram_id: int):
    return main_menu_kb(await get_user_locale(telegram_id))
