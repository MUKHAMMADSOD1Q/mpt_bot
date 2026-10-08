from bot.database import get_user
from bot.i18n import normalize_language
from bot.keyboards import main_menu_kb


async def localized_main_menu(telegram_id: int):
    user = await get_user(telegram_id)
    return main_menu_kb(normalize_language(user.get("lang") if user else None))
