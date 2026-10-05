import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")

# Railway'da Volume ulasangiz: DB_PATH=/data/mpt_bot.db (Volume mount yo'li /data bo'lsa)
DB_PATH = os.getenv("DB_PATH") or os.path.join(os.path.dirname(os.path.dirname(__file__)), "mpt_bot.db")

# 1 MPT narxi (so'mda)
MPT_PRICE_SOM = 200

# Ta'rif turlari: nomi -> (1 sahifa uchun MPT, 1 sahifa uchun so'm)
TARIFFS = {
    "bepul": {"title": "Bepul", "mpt": 0, "som": 0},
    "start": {"title": "Start", "mpt": 10, "som": 2000},
    "standart": {"title": "Standart", "mpt": 22.5, "som": 4500},
    "smart": {"title": "Smart", "mpt": 32.5, "som": 6500},
    "pro": {"title": "Pro", "mpt": 40, "som": 8000},
    "elite": {"title": "Elite", "mpt": 50, "som": 10000},
    "maxsus": {"title": "MAXSUS", "mpt": 100, "som": 20000},
}

# Oylik/yillik obuna tariflari: nomi -> (narx_som, ochiladigan_tariflar_royxati)
SUBSCRIPTIONS = {
    "1oy": {"title": "Bir oylik", "days": 30, "som": 180_000, "unlocks": ["bepul", "start"]},
    "3oy": {"title": "Uch oylik", "days": 90, "som": 520_000, "unlocks": ["bepul", "start", "standart"]},
    "6oy": {"title": "Yarim yillik", "days": 182, "som": 1_060_000, "unlocks": ["bepul", "start", "standart", "smart", "pro"]},
    "9oy": {"title": "To'qqiz oylik", "days": 274, "som": 1_580_000, "unlocks": ["bepul", "start", "standart", "smart", "pro", "elite", "maxsus"]},
    "12oy": {"title": "Yillik", "days": 365, "som": 2_150_000, "unlocks": list(TARIFFS.keys())},
}

MIN_PAGES = 1
MAX_PAGES = 50

# ---- CLICK Merchant API ----
# merchant.click.uz shaxsiy kabinetingizdagi "Shop API" bo'limidan olinadi
CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID", "")
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID", "")
CLICK_MERCHANT_USER_ID = os.getenv("CLICK_MERCHANT_USER_ID", "")
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "")

# ---- Bot egasi (siz) — /admin buyrug'i FAQAT shu ID uchun ishlaydi ----
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# ---- Uch xil ishchi guruh ----
# 1) Yangi buyurtmalar (dastlabki ma'lumot + ikki marta tasdiqlangач "Qabul qilindi")
ORDERS_GROUP_ID = int(os.getenv("ORDERS_GROUP_ID", "-1002397917281"))
# 2) To'lovlar (karta chekini adminlar tasdiqlaydi / Click avtomatik tasdiqlanadi)
PAYMENT_GROUP_ID = int(os.getenv("PAYMENT_GROUP_ID", "-1003180457594"))
# 3) Userlar fayllari (tayyor ish shu yerga yuklanadi, bot userga yo'naltiradi)
FILES_GROUP_ID = int(os.getenv("FILES_GROUP_ID", "-1004449440402"))

# ---- To'g'ridan-to'g'ri kartaga o'tkazma uchun karta raqamlari ----
CARD_NUMBERS = {
    "UzCard": ["5614 6812 5986 8051", "5614 6821 1052 3232"],
    "Humo": ["9860 1701 0410 8668", "9860 3501 4163 6620"],
    "VISA": ["4916 9903 0807 1304", "4023 0605 1818 5649", "4413 5976 0320 4007"],
    "MasterCard": ["5217 3959 0687 0052"],
}
CARD_OWNER_NAME = "Muhammadsodiq"

# Karta to'lovi uchun ajratilgan vaqt (soniyada) - shundan keyin "5 daqiqa qo'shish / bekor qilish" so'raladi
CARD_PAYMENT_TIMEOUT_SECONDS = 5 * 60

# ---- AI xizmatlari (ixtiyoriy — sozlanmasa, tegishli funksiyalar o'chiq turadi) ----
# Chekni tekshirish uchun (rasm/PDF tushunadi, bepul kvotasi bor): https://aistudio.google.com/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Matn/slayd kontenti generatsiyasi uchun (arzon, katta hajmda): https://platform.deepseek.com
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ---- soff.uz sotuvchi sahifangiz ----
SOFF_SELLER_ID = os.getenv("SOFF_SELLER_ID", "879")
SOFF_SELLER_PANEL_URL = "https://seller.soff.uz/seller/products"
SOFF_SELLER_PAGE_URL = f"https://soff.uz/seller/{SOFF_SELLER_ID}"

# Har bir sahifada nechta mahsulot ko'rsatiladi
SOFF_PAGE_SIZE = 10

# ---- Aloqa va "biz haqimizda" ma'lumotlari ----
CONTACT = {
    "founder_dev": "https://t.me/MUKHAMMADSODlQ",
    "founder_dev_extra": "https://t.me/MUHAMMADS0DlQ",
    "support": "https://t.me/preuzadmin",
    "phones": ["+998996665732", "+998901995732", "+998942881488"],
}

# ---- Mustaqil ishlar (referat/mustaqil ish/kurs ishi) — 1 sahifa narxi (so'm) ----
INDEPENDENT_WORK_TYPES = {
    "referat": {"title": "Referat", "price_per_page": 5000},
    "mustaqil_ish": {"title": "Mustaqil ish", "price_per_page": 8000},
    "kurs_ishi": {"title": "Kurs ishi", "price_per_page": 10000},
    "boshqa": {"title": "Boshqa (admin bilan kelishiladi)", "price_per_page": None},
}
# O'zbek tilidan boshqa har qanday tilda bajarilsa, 1 sahifaga qo'shimcha narx (so'm)
LANGUAGE_SURCHARGE_PER_PAGE = 1000
WORK_LANGUAGES = ["O'zbek", "Rus", "Ingliz", "Boshqa"]

# ---- "Tadbirkorlar uchun" xizmatlari narxlari ----
TAKLIFNOMA_PRICE = 50_000
REZYUME_PRICE = 50_000
YOUTUBE_BANNER_PRICE = 50_000
QR_GENERATOR_PRICE = 30_000
UI_DESIGN_PRICE_RANGE = (500_000, 3_000_000)
LOGO_PRICE_RANGE = (100_000, 5_000_000)
WEBSITE_STYLE_PRICES = {
    "minimalizm": (1_000_000, 2_000_000),
    "zamonaviy": (2_000_000, 4_000_000),
    "hi-tech": (4_000_000, 7_000_000),
    "3d": (7_000_000, 10_000_000),
    "boshqa": None,  # admin bilan kelishiladi
}
