from bot.config import TARIFFS, MPT_PRICE_SOM, LANGUAGE_SURCHARGE_PER_PAGE


def is_uzbek(language: str | None) -> bool:
    if not language:
        return True
    lang = language.strip().lower().replace("‘", "'").replace("’", "'").replace("`", "'")
    return lang.startswith("o'zbek") or lang.startswith("ozbek") or lang in ("uz", "uzbek")


def calculate_price(tariff_key: str, pages: int, language: str | None = None) -> dict:
    """Taqdimot narxi. O'zbek tilidan boshqa tilda bo'lsa, sahifasiga +1000 so'm
    (MPT da +5) qo'shiladi — "Bepul" ta'rif bundan mustasno."""
    tariff = TARIFFS[tariff_key]
    surcharge_som = 0
    if tariff_key != "bepul" and not is_uzbek(language):
        surcharge_som = LANGUAGE_SURCHARGE_PER_PAGE
    per_page_som = tariff["som"] + surcharge_som
    per_page_mpt = tariff["mpt"] + surcharge_som / MPT_PRICE_SOM
    return {
        "tariff_title": tariff["title"],
        "pages": pages,
        "price_per_page_som": per_page_som,
        "surcharge_per_page_som": surcharge_som,
        "price_som": per_page_som * pages,
        "price_mpt": per_page_mpt * pages,
    }


def format_som(value: float) -> str:
    return f"{int(value):,}".replace(",", ".")
