from bot.config import TARIFFS


def calculate_price(tariff_key: str, pages: int) -> dict:
    tariff = TARIFFS[tariff_key]
    total_som = tariff["som"] * pages
    total_mpt = tariff["mpt"] * pages
    return {
        "tariff_title": tariff["title"],
        "pages": pages,
        "price_som": total_som,
        "price_mpt": total_mpt,
    }


def format_som(value: float) -> str:
    return f"{int(value):,}".replace(",", ".")
