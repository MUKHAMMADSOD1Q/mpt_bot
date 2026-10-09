# MPT Bot — Taqdimot/Referat/Xizmatlar Telegram-boti

Bu loyiha sizning `PreuzMPT.docx` va `prezintatsiya.uz` TZ fayllaringiz asosida tuzilgan
**ishga tushirishga tayyor boshlang'ich (MVP) kod**. U quyidagilarni bajaradi:

- `/start` va asosiy menyu
- Taqdimotga to'liq buyurtma oqimi (mavzu → sahifa soni → ism → muassasa → yo'nalish → til → tarif → narx hisoblash → tasdiqlash)
- 7 xil tarif (Bepul, Start, Standart, Smart, Pro, Elite, MAXSUS) va ularning MPT/so'm narxlari
- Oylik/yillik obuna tariflari
- Foydalanuvchi uchun MPT balans tizimi (SQLite bazasida)
- Admin uchun buyruqlar: balans qo'shish, obuna faollashtirish, buyurtmalarni ko'rish/bajarish/rad etish
- Admin paneldan foydalanuvchilarning Telegram ismi, aloqa/balans/obuna ma'lumotlari va buyurtmalar tarixini Excel (`.xlsx`) ko'rinishida olish
- Gemini API ulanganida, to'langan taqdimotlarni shablon asosida AI matni bilan to'ldirib foydalanuvchiga avtomatik yuborish
- "Boshqa xizmatlar" (Logo, QR, Taklifnoma va h.k.) uchun to'g'ridan-to'g'ri adminga yo'naltirish
- Kelajakda kengaytirish uchun shablon-asosida PowerPoint generatsiya moduli (`bot/services/pptx_generator.py`)

Quyida **nolldan production'gacha** bo'lgan barcha qadamlar yozilgan.

---

## 1. Nima uchun aynan shu texnologiyalar tanlandi

| Tanlov | Sabab |
|---|---|
| **Python 3.11+** | Telegram-botlar uchun eng katta community, `python-pptx` va `python-docx` kutubxonalari orqali taqdimot/hujjat generatsiyasini to'g'ridan-to'g'ri kod ichida qilish mumkin — sizga aynan shu kerak. |
| **aiogram 3.x** | Hozirgi eng zamonaviy, async, FSM (foydalanuvchi bilan qadam-baqadam suhbat) qo'llab-quvvatlaydigan Telegram bot freymvorki. Rasmiy hujjatlari juda yaxshi: https://docs.aiogram.dev |
| **SQLite (aiosqlite)** | Boshlang'ich bosqich uchun alohida server kerak emas, fayl sifatida ishlaydi. 10K+ obunachi bilan ham boshida yetadi. Keyinchalik yuk oshsa PostgreSQL'ga ko'chirish oson. |

> Siz Flutter/Dart bilan ishlaysiz — bu yaxshi, lekin Telegram bot backend'i uchun Dart emas,
> Python tavsiya etiladi, chunki hujjat/taqdimot generatsiya kutubxonalari va bot community'si
> Python'da ancha boy. Flutter bilimingiz kelajakda botga mini-app (Telegram WebApp) frontend
> yozishda juda qo'l keladi — buni pastda "Keyingi qadamlar" bo'limida tushuntirdim.

---

## 2. Dasturlash muhitini sozlash

1. **Python o'rnatish** (agar yo'q bo'lsa): https://www.python.org/downloads/ dan 3.11 yoki undan yuqori versiyani o'rnating.
2. **VS Code** sizda bor — unga faqat **Python** va **Pylance** kengaytmalarini o'rnating (Extensions bo'limidan).
3. **Git** sizda bor — hisobingiz bo'lmasa GitHub'da akkaunt oching.
4. Loyihani papkaga oching:
   ```bash
   cd mpt_bot
   python3 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. `.env.example` faylini `.env` deb nusxalang va to'ldiring:
   ```bash
   cp .env.example .env
   ```
   - `BOT_TOKEN` — Telegram'da **@BotFather** ga `/newbot` yuboring (yoki mavjud botingiz bo'lsa `/mybots` → Bot → API Token) va tokenni shu yerga qo'ying.
   - `ADMIN_IDS` — o'z Telegram ID raqamingizni **@userinfobot** orqali bilib oling.
   - `ADMIN_USERNAME` — sizning (yoki admin akkauntingiz) username'i, `@` belgisiz.

6. Botni lokal ishga tushiring:
   ```bash
   python main.py
   ```
   Telegram'da botingizga `/start` yuboring — javob bersa, hammasi to'g'ri sozlangan.

### AI yordamida taqdimot tayyorlash

1. Asosiy menyudagi **⚙️ Sozlamalar → 🌐 Tilni sozlash** orqali interfeys tilini tanlang:
   o'zbek, rus, ingliz, tojik, qozoq, qirg'iz yoki turkman.
2. **🤖 Sun'iy intellekt yordamida** bo'limida mavzu, sahifalar soni va titul sahifasi
   ma'lumotlarini kiriting. Sahifalar soniga titul va yakuniy «RAHMAT!» sahifalari ham kiradi;
   taqdimot kamida 3 sahifali bo'lishi kerak. Bot AI promptni alohida, nusxalashga qulay
   monospace blokda beradi.
3. Promptni o'zingiz ishonadigan AI xizmatiga yuboring va qaytgan matnni botga jo'nating.
   Matnda umumiy sahifalar sonidan 2 ta kam abzats bo'lishi kerak (titul va yakuniy sahifa
   uchun matn yozilmaydi); uzun matnni UTF-8 `.txt` fayl qilib yuborish mumkin.
4. Rasmlar ixtiyoriy: istalgancha yuborish va tugatish tugmasi bilan ertaroq yakunlash mumkin.
   Rasmlar kontent sahifalariga taqsimlanadi.
5. Bot `assets/templates/bepul/1.pptx`, `2.pptx`, `3.pptx` shablonlaridan tasodifiy birini
   tanlab taqdimotni tayyorlaydi. Fayl avval fayllar guruhiga ko'rib chiqish uchun yuboriladi;
   administrator tasdiqlagandan keyingina foydalanuvchiga yetkaziladi.
6. Oddiy buyurtmadagi bepul tarifda, Gemini API sozlangan bo'lsa, avtomatik generatsiya
   avvalgidek ishlashi mumkin. Buning uchun [Google AI Studio](https://aistudio.google.com/apikey)
   dan `GEMINI_API_KEY` oling va uni lokal `.env` yoki Railway **Variables** bo'limiga kiriting.
   Kalitni chatga yoki GitHub'ga yubormang.

Til sozlamasi foydalanuvchiga ko'rinadigan bot interfeysi va asosiy suhbat oqimlarini
yetti tilda — o'zbek, rus, ingliz, tojik, qozoq, qirg'iz va turkman tillarida —
mahalliylashtiradi. Bunga taqdimot va PreCal, mustaqil ish, biznes xizmatlari, tayyor
mahsulotlarni ko'rish, balans/obuna, Click/karta to'lovi, tasdiqlash va fayl yetkazish
xabarlari hamda tugmalar kiradi. Admin paneli va buyurtma/to'lov/fayl guruhlariga
yuboriladigan ichki xabarlar o'zbekcha qoladi; foydalanuvchi kiritgan ma'lumotlar
asl holida ko'rsatiladi.

Qo'lda AI oqimida bot tashqi AI xizmatiga o'zi ulanmaydi: promptni foydalanuvchi tanlagan
xizmatga foydalanuvchining o'zi yuboradi. Javob matni va tanlangan rasmlardan tayyorlangan
`.pptx` avval fayllar guruhiga admin ko'rigi uchun yuboriladi. Foydalanuvchiga fayl faqat
admin **Tasdiqlash va yuborish** tugmasini bosgandan keyin yetkaziladi.

Gemini'ning bepul API kvotasi model va loyiha bo'yicha o'zgaradi; aniq joriy RPM/RPD limitini
[AI Studio rate limits](https://aistudio.google.com/rate-limit) sahifasida tekshiring.
Bepul xizmatda yuborilgan matnlar Google mahsulotlarini yaxshilash uchun ishlatilishi mumkin.
Bot AI'ga mavzu va tilni yuboradi, ism/Telegram ID/telefon yubormaydi.

---

## 3. Kod tuzilishi

```
mpt_bot/
├── main.py                        # Botni ishga tushiruvchi fayl (polling)
├── requirements.txt
├── .env.example
├── bot/
│   ├── config.py                  # Tariflar, narxlar, sozlamalar (.env dan o'qiydi)
│   ├── database.py                # SQLite bilan ishlash (foydalanuvchi, buyurtma, balans)
│   ├── keyboards.py                # Barcha tugmalar (inline/reply)
│   ├── states.py                   # FSM holatlari (foydalanuvchi qaysi bosqichda)
│   ├── handlers/
│   │   ├── start.py                # /start, asosiy menyu, "boshqa xizmatlar"
│   │   ├── presentation_order.py   # Taqdimotga buyurtma — to'liq FSM oqimi
│   │   ├── independent_work.py     # Mustaqil ish/referat (hozircha admin'ga yo'naltiradi)
│   │   ├── balance.py               # MPT balans va obuna sotib olish
│   │   └── admin.py                 # Admin buyruqlari (/addmpt, /addsub, /orders)
│   └── services/
│       ├── validators.py            # TZ'dagi barcha kiritish qoidalari (ism, sahifa, mavzu)
│       ├── pricing.py               # Narx hisoblash formulasi
│       └── pptx_generator.py        # Shablon-asosida PowerPoint generatsiya (MVP)
```

Har bir fayl mustaqil va izohlangan — TZ'dagi validatsiya qoidalarining barchasi
`validators.py` faylida amalga oshirilgan (masalan, bitta harfli ism rad etiladi,
51 sahifadan ko'p qabul qilinmaydi va h.k.).

---

## 4. To'lov tizimi haqida muhim eslatma

Hozirgi MVP'da to'lov ikki xil ishlaydi (aynan siz so'ragan tartibda):

1. **MPT balansi orqali** — foydalanuvchi oldindan MPT sotib olgan bo'lsa, buyurtma
   tasdiqlanganda balansidan avtomatik yechiladi.
2. **To'g'ridan-to'g'ri adminga murojaat** — agar balans yetmasa, bot foydalanuvchiga
   va sizga (admin) xabar yuboradi, siz to'lovni qabul qilib, `/addmpt <id> <miqdor>`
   buyrug'i bilan balansni qo'lda to'ldirasiz.

Bu — 10K+ obunachi bilan ishni **hoziroq, hech qanday bank shartnomasisiz** boshlash
uchun eng tez yo'l. Keyinchalik avtomatlashtirish uchun:

- **Payme Merchant API** yoki **Click Merchant API**'ni ulang (ikkalasi ham O'zbekistonda
  eng ko'p ishlatiladigan usul, hujjatlari: https://developer.help.paycom.uz va
  https://docs.click.uz). Bular uchun tadbirkor sifatida ro'yxatdan o'tish va merchant
  hisobi kerak bo'ladi.
- Ulanganda, `bot/handlers/balance.py` ichidagi `subscription_chosen` va
  `presentation_order.py` ichidagi to'lov qismini shu API chaqiruviga almashtirasiz.

---

## 5. Botni bepul serverga qo'yish (deploy)

Eng oson va ishonchli bepul variantlar — **Railway** yoki **Render** (ikkalasi ham
GitHub bilan bevosita integratsiya qiladi):

### Variant A — Railway.app (tavsiya etiladi, sozlash eng tez)

1. Loyihani GitHub'ga yuklang:
   ```bash
   cd mpt_bot
   git init
   git add .
   git commit -m "Boshlang'ich MPT bot"
   git branch -M main
   git remote add origin https://github.com/<username>/mpt-bot.git
   git push -u origin main
   ```
   (`.env` fayli `.gitignore`da bor — u GitHub'ga yuklanmaydi, bu xavfsizlik uchun to'g'ri.)
2. https://railway.app ga GitHub akkauntingiz bilan kiring.
3. **New Project → Deploy from GitHub repo** → `mpt-bot` repongizni tanlang.
4. **Variables** bo'limida `.env` faylidagi barcha qiymatlarni (`BOT_TOKEN`, `ADMIN_IDS`,
   `ADMIN_USERNAME`) qo'lda kiriting.
5. Railway `Procfile`ni avtomatik topib, `python main.py`ni **worker** sifatida ishga
   tushiradi. Bepul tarifda oyiga ma'lum miqdor kredit beriladi — kichik botlar uchun yetarli.

### Variant B — Render.com

1. Xuddi shu tarzda GitHub'ga yuklang.
2. Render'da **New → Background Worker** yarating, repongizni ulang.
3. Build command: `pip install -r requirements.txt`
   Start command: `python main.py`
4. Environment Variables bo'limiga `.env`dagi qiymatlarni kiriting.

### Variant C — O'zingizning VPS (masalan Oracle Cloud Free Tier, doimiy bepul)

Agar to'liq nazorat va cheklovsiz ishlashni istasangiz:
```bash
ssh user@server_ip
git clone https://github.com/<username>/mpt-bot.git
cd mpt-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # va to'ldiring
# Botni doim ishlab turishi uchun systemd yoki tmux/screen orqali ishga tushiring:
nohup python main.py &
```
Yaxshiroq yechim — `systemd` service yaratish, shunda server qayta yoqilganda bot
avtomatik qayta ishga tushadi (so'rasangiz, buning uchun tayyor `.service` faylini
ham yozib beraman).

---

## 6. Keyingi qadamlar (rivojlantirish yo'l xaritasi)

1. **PowerPoint generatsiyasini to'liq ishga tushirish** — `assets/` papkasiga tayyor
   shablon `.pptx` fayllaringizni joylang, ularda `{{TOPIC}}`, `{{FULLNAME}}`,
   `{{INSTITUTION}}`, `{{DIRECTION}}` kabi maxsus so'zlarni matn qutilariga yozing.
   `pptx_generator.build_presentation()` funksiyasi ularni avtomatik to'ldiradi va
   kerakli sahifa soniga qadar ko'paytiradi. Buyurtma tasdiqlangach, shu funksiyani
   chaqirib, tayyor faylni foydalanuvchiga `bot.send_document()` orqali yuborasiz.
2. **AI-yordamida matn generatsiya** — Claude API (yoki boshqa LLM) orqali har bir
   slayd/referat uchun mazmunli matn generatsiya qilishni `generate_slide_content()`
   funksiyasiga ulash. Bu "Sun'iy intellekt yordamida" bo'limini to'liq ishga tushiradi.
3. **Payme/Click integratsiyasi** — yuqorida 4-bo'limda tavsiya qilingan.
4. **Mustaqil ish/referat uchun Word (.docx) generatsiyasi** — xuddi pptx kabi,
   `python-docx` bilan shablon-asosida ishlaydigan modul qo'shish (`docx_generator.py`).
5. **QR-skaner xizmati** — bu odatda foydalanuvchi rasm yuboradi, bot uni
   `pyzbar`/`opencv-python` bilan o'qib beradi. Alohida handler sifatida qo'shsa bo'ladi.
6. **Katta trafik uchun webhook rejimi** — 10K+ obunachi faollashsa, `polling` o'rniga
   `webhook` rejimiga o'tish tavsiya etiladi (aiogram buni to'liq qo'llab-quvvatlaydi,
   FastAPI/aiohttp bilan birga ishlaydi).
7. **Ma'lumotlar bazasini kattalashtirish** — foydalanuvchilar soni ko'payib, buyurtmalar
   soni oshsa, SQLite'dan PostgreSQL'ga o'tish tavsiya etiladi (Railway/Render'da bepul
   PostgreSQL instance mavjud).
8. **Flutter bilimingizni ishlatish** — Telegram bot ichida **Mini App (WebApp)** sifatida
   Flutter Web bilan chiroyli interfeys (masalan, tarif tanlash, shablon ko'rish galereyasi)
   qo'shishingiz mumkin — bu sizning kuchli tomoningiz, va aynan sizning TZ hujjatingizda
   "miniApp" so'zi tilga olingan, demak buni allaqachon rejalashtirgansiz.

---

## 7. Xavfsizlik bo'yicha eslatmalar

- `.env` faylini hech qachon GitHub'ga yoki boshqa ochiq joyga yubormang — u sizning
  bot tokeningizni o'z ichiga oladi.
- Admin buyruqlari (`/addmpt`, `/addsub`) faqat `OWNER_ID`, `ADMIN_IDS` yoki superadmin
  panelidan tayinlangan adminlar uchun ishlaydi. Admin huquqini faqat ishonchli akkauntlarga bering.
- Production'ga chiqishdan oldin, `main.py` ichidagi `logging.basicConfig(level=logging.INFO)`
  darajasini kamaytiring va xatoliklarni fayllarga yozib borishni sozlang.

---

## 8. YANGI QO'SHILGAN IMKONIYATLAR (2-bosqich)

### 8.1 Ikkita to'lov usuli — Click va Karta

Endi har qanday to'lov (MPT sotib olish, obuna, buyurtma) so'ralganda foydalanuvchiga
**"💳 Click orqali" / "🏦 Kartaga to'lov"** tanlovi chiqadi (`bot/services/payment_common.py`).

- **Click** — avvalgidek Invoice API orqali (telefon raqamiga to'lov so'rovi + "Tekshirish" tugmasi).
- **Karta** — `bot/config.py` ichidagi `CARD_NUMBERS` ro'yxatidagi (UzCard/Humo/VISA/MasterCard)
  kartalaringiz ko'rsatiladi, foydalanuvchi telefon raqamini kiritadi, o'tkazma qilgach
  **chek (skrinshot yoki PDF)** yuboradi.

Chek kelgach avtomatik ravishda **Gemini AI** orqali tekshiriladi (`bot/services/ai_verify.py`):
summasi va sanasi mos kelsa — **avtomatik tasdiqlanadi**; shubhali/mos kelmasa —
sizga (barcha `ADMIN_IDS`) chek rasmi + "✅ Tasdiqlash / ❌ Rad etish" tugmalari bilan yuboriladi.

**Buni ishga tushirish uchun:**
1. https://aistudio.google.com/apikey ga kirib, bepul API kalit oling.
2. `.env` fayliga qo'shing: `GEMINI_API_KEY=...`
3. Tayyor! Kalit bo'lmasa ham bot ishlayveradi — faqat AI tekshiruvi o'chiq turadi va
   har bir chekni siz qo'lda tasdiqlaysiz (bu ham to'liq ishlaydi).

> **Diqqat:** Gemini javobidagi "to'landi/haqiqiy" xulosasi ehtimoliy baholash, 100%
> kafolat emas — katta summalarda baribir o'zingiz ko'zdan kechirib turishni tavsiya
> qilaman, ayniqsa boshida.

### 8.2 Admin/User rejimi va adminlarni boshqarish

`/admin` buyrug'ini `OWNER_ID`, `ADMIN_IDS` yoki superadmin tayinlagan admin yuborsa,
bot shu akkaunt uchun **Admin menyu**ni ochadi:

- 📊 **Statistika** — foydalanuvchilar soni, Click/Karta orqali qayd etilgan to'lovlar yig'indisi
- 👤 **Foydalanuvchiga xabar** — ID bo'yicha bittaga; matn yoki fayl/media
- 📢 **Barchaga xabar** — hamma foydalanuvchiga; xabar ham, fayl/media ham yuboriladi
- 🧾 **Kutayotgan buyurtmalar**
- 🛍 **Soff.uz'ga yuklash** — eslatma/havola (pastga qarang)
- 👥 **Adminlarni boshqarish** — faqat superadmin ko'radi; `/addadmin TELEGRAM_ID`
  va `/removeadmin TELEGRAM_ID` buyruqlari bilan tayinlash/bekor qilish
- 🔙 **Oddiy rejimga qaytish**

`.env` faylida `OWNER_ID` ni o'zingizning Telegram ID'ingizga o'rnating.
Tayinlangan adminlar bazada saqlanadi. Tayyor fayllar guruhida ham tayinlangan adminlar
buyurtma xabariga reply qilib yoki `/send order-ID` / `/send service-ID` bilan fayl yuborishi mumkin.

**Muhim cheklov:** Bot orqali sizning haqiqiy **bank/karta balansingizni** ko'rish
imkonsiz — buning uchun bank bilan rasmiy API shartnomasi kerak bo'ladi (YaTT
sifatida buni so'rashingiz mumkin, lekin odatda faqat yirik tashkilotlarga beriladi).
"📊 Statistika" faqat **bot orqali o'tgan va tasdiqlangan to'lovlar yozuvini**
ko'rsatadi — bu aniq buxgalteriya emas, informatsion ko'rsatkich.

### 8.3 To'lov tasdiqlari guruhi

Har bir muvaffaqiyatli to'lovdan so'ng, siz bergan formatda ("Ism / Username / Telefon /
Prezentatsiya turi va h.k. / ✅ Qabul qilindi") xabar avtomatik guruhingizga yuboriladi.

**Sozlash:**
1. Botni guruhingizga admin sifatida qo'shing (xabar yuborishi uchun kamida oddiy
   a'zolik yetarli, lekin admin qilib qo'yish tavsiya etiladi).
2. Guruh ichida botga `/groupid` buyrug'ini yuboring (faqat siz uchun ishlaydi).
3. Chiqqan raqamni `.env` fayliga yozing: `PAYMENT_GROUP_ID=-100xxxxxxxxxx`

### 8.4 Shablonlarni qayerga va qanday yuklash kerak

**Format: albatta `.pptx`** (PowerPoint) — sababi `pptx_generator.py` faylida yozilgan:
`python-pptx` kutubxonasi matn qutilarini formatni buzmasdan dasturiy almashtira oladi;
PDF yoki rasm-eksport formatlarida bu deyarli imkonsiz.

**Qayerga qo'yish:**
```
assets/templates/bepul/1.pptx ... 10.pptx
assets/templates/start/1.pptx ... 10.pptx
assets/templates/standart/1.pptx ... 10.pptx
assets/templates/smart/1.pptx ... 10.pptx
assets/templates/pro/1.pptx ... 10.pptx
assets/templates/elite/1.pptx ... 10.pptx
assets/templates/maxsus/1.pptx ... 10.pptx
```
(papka nomlari `bot/config.py`dagi `TARIFFS` kalitlari bilan bir xil bo'lishi shart)

**Har bir shablon ichida** matn qutilariga aynan shu so'zlarni yozing (katta-kichik harf muhim):
```
{{TOPIC}}        -> taqdimot mavzusi shu yerga yoziladi
{{FULLNAME}}     -> talabaning ismi
{{INSTITUTION}}  -> o'quv muassasasi
{{DIRECTION}}    -> yo'nalish/guruh
```
Bular oddiy matn sifatida (masalan sarlavha joyiga) yozilishi kifoya — dizayn, shrift,
rang, fon o'zgarmaydi, faqat matn almashadi.

To'lov tasdiqlanib, admin "✅ Bajarildi" tugmasini bosganda (`bot/handlers/admin.py`,
`admin_mark_done`), bot avtomatik ravishda tanlangan tarif papkasidan **tasodifiy**
bitta shablonni oladi, ma'lumotlarni to'ldiradi va foydalanuvchiga **to'g'ridan-to'g'ri
yuboradi** — foydalanuvchi qaysi shablon ishlatilganini bilmaydi. Agar shu tarif uchun
hali shablon yuklamagan bo'lsangiz, bot eski xatti-harakatga qaytadi (shunchaki
"tayyor" xabari, faylni o'zingiz qo'lda yuborasiz).

### 8.5 soff.uz — tayyor mahsulotlar ro'yxati

Foydalanuvchi menyusida **"🛍 Tayyor mahsulotlar"** tugmasi qo'shildi — 10 tadan
ko'rsatadi, Oldingi/Keyingi va Qidirish tugmalari bilan.

**MUHIM:** soff.uz sahifasi JavaScript orqali yuklanadigan (Next.js) sayt, shuning
uchun men mahsulotlar ro'yxatini olish kodini (`bot/services/soff_client.py`) eng
keng tarqalgan usul (`__NEXT_DATA__` degan yashirin JSON) asosida yozdim, lekin buni
100% ishlashini siz tomondan tasdiqlash kerak:

1. `python debug_soff.py` buyrug'ini ishga tushiring (loyiha papkasida, venv faol holda).
2. Agar `soff_debug_next.json` fayli hosil bo'lsa va ichida mahsulot nomlari/narxlari
   ko'rinsa — tayyor, bot ishlayveradi.
3. Agar hosil bo'lmasa (yoki bo'sh bo'lsa) — brauzeringizda soff.uz sahifasini oching,
   F12 > Network > Fetch/XHR bo'limidan mahsulotlar JSON qaytaradigan so'rovni toping
   va uning to'liq manzilini (Request URL) menga yuboring — `soff_client.py` faylini
   aynan shu API'ga moslab yangilayman.

**Mahsulot yuklash (admin panelidan seller.soff.uz'ga)** — bu sayt sizniki bo'lgani
uchun, agar avtorizatsiya/yuklash API'si haqida ma'lumot (login oqimi, so'rov
formati) bersangiz, "🛍 Soff.uz'ga yuklash" tugmasini to'liq avtomatlashtirib
beraman (hozircha faqat panelga havola beradi).

### 8.6 AI generatsiya — eng arzon variantlar

| Vazifa | Tavsiya | Narx/limit | Sozlash |
|---|---|---|---|
| **Chek tekshirish** (rasm/PDF tushunish) | Google **Gemini** | Bepul kvota mavjud; aniq so'rov/token limiti AI Studio loyihasiga qarab o'zgaradi | `.env`: `GEMINI_API_KEY` |
| **Taqdimot matni va PPTX** | Google **Gemini 2.5 Flash** | Bepul tier'da input/output tokenlar bepul; aniq joriy RPM/RPD limit AI Studio'da ko'rinadi | `.env`: `GEMINI_API_KEY` |

Taqdimot generatsiyasi `bot/services/ai_content.py` orqali bir marta strukturali JSON
so'rov yuboradi. Gemini limiti tugasa yoki kalit sozlanmagan bo'lsa, buyurtma to'lov
qilingan holatda qoladi va fayllar guruhida qo'lda tayyorlash uchun ko'rsatiladi.
Gemini bepul tarifida tokenlar bepul bo'ladi, ammo bu cheksiz foydalanish degani emas:
model limitlari o'zgaradi va AI Studio'da ko'rinadi. OpenAI va xAI/Grok API'da narxlar
foydalanilgan tokenlarga qarab belgilanadi; akkauntga xos bepul kredit yoki aksiya bor-yo'qligini
provider panelidan tekshiring. Rasmiy sahifalar:
[Gemini narxlari](https://ai.google.dev/gemini-api/docs/pricing),
[Gemini limitlari](https://ai.google.dev/gemini-api/docs/rate-limits),
[OpenAI API narxlari](https://developers.openai.com/api/docs/pricing),
[xAI narxlari](https://docs.x.ai/developers/pricing).

### 8.7 Server: Supabase haqida muhim eslatma

**Supabase bilan botni to'g'ridan-to'g'ri "joylab" bo'lmaydi** — Supabase bu
ma'lumotlar bazasi + fayl xotira (storage) + autentifikatsiya xizmati (BaaS), u
sizning doimiy ishlab turadigan Python botingizni (polling rejimida) ishga
tushiradigan compute (protsessor vaqti) taklif qilmaydi.

**Tavsiya etilgan kombinatsiya:**
- **Ma'lumotlar bazasi**: boshida SQLite (hozirgi holat) yetarli. Foydalanuvchilar
  ko'payib, bir vaqtda ko'p yozish kerak bo'lsa — Supabase'ning bepul **Postgres**
  bazasiga o'ting (500MB bepul, keyin arzon). Fayl xotira (chek rasmlari, shablonlar)
  uchun Supabase **Storage** juda mos — bepul 1GB.
- **Botni ishga tushirish (compute)**: baribir Railway/Render/Fly.io kabi joy kerak
  (5-bo'limda yozilgan). Bular bepul tarifda ham botni 24/7 ishlatadi.

Xulosa: **Supabase (baza+fayl) + Railway/Render (bot protsessi)** — bu ikkalasi
birga eng oqilona bepul boshlanish. Xohlasangiz, SQLite'dan Supabase Postgres'ga
o'tish kodini alohida yozib beraman (`asyncpg` yoki `supabase-py` bilan).

### 8.8 Yangi .env o'zgaruvchilari (qisqacha jamlanma)

```
OWNER_ID=...              # sizning Telegram ID'ingiz - /admin shu uchun ishlaydi
PAYMENT_GROUP_ID=...      # /groupid orqali oling
GEMINI_API_KEY=...        # chek tekshirish va PPTX matni generatsiyasi
DEEPSEEK_API_KEY=...      # boshqa mavjud DeepSeek integratsiyalari uchun
```

Karta raqamlari va admin ismi hozircha `bot/config.py` ichida to'g'ridan-to'g'ri
yozilgan (`CARD_NUMBERS`, `CARD_OWNER_NAME`) — xohlasangiz shu faylda o'zgartirasiz.

---

## 9. ESKI BAZANI KO'CHIRISH, GITHUB'GA YUKLASH VA RAILWAY'GA JOYLASH

### 9.1 Eski foydalanuvchilar bazasini import qilish

Eski botingizdagi `DataBase.db` faylida **8 340 ta noyob foydalanuvchi**, ularning
telefon raqamlari (bo'lsa), tili, eski buyurtmalar tarixi va 15 ta tayyor mahsulot bor.
Bularni yangi botga qo'shish uchun:

1. Botni ishga tushiring (lokal yoki serverda) va o'zingiz (`OWNER_ID`) shaxsiy chatda botga yozing.
2. `DataBase.db` faylini botga **hujjat (fayl) sifatida** yuboring, izoh (caption) qismiga
   aynan `/importdb` deb yozing.
3. Bot faylni tekshirib, avtomatik import qiladi va hisobot beradi (nechta yangi
   foydalanuvchi qo'shildi, nechtasi allaqachon bor edi, nechtasida haqiqiy telefon
   raqami bor va h.k.).
4. Import **qayta-qayta xavfsiz ishga tushirilishi mumkin** — mavjud foydalanuvchilar
   ustidan yozilmaydi, faqat bo'sh maydonlar to'ldiriladi.
5. Eski bazadagi 4 ta admin ID hisobotda ko'rsatiladi — ularni admin qilmoqchi
   bo'lsangiz, superadmin panelidagi **Adminlarni boshqarish** orqali tayinlang.

MPT balansi eski bazada yo'q edi, shuning uchun barcha import qilingan foydalanuvchilar
balansi `0` dan boshlanadi — xohlasangiz `/addmpt` orqali qo'lda qo'shib chiqishingiz mumkin.

### 9.2 GitHub'ga yuklash

```bash
cd mpt_bot
git init
git add .
git commit -m "MPT bot - to'liq versiya"
git branch -M main
git remote add origin https://github.com/<username>/mpt-bot.git
git push -u origin main
```

`.gitignore` fayli `.env` va `*.db` fayllarni avtomatik chetlab o'tadi — tokeningiz va
foydalanuvchilar bazangiz GitHub'ga **hech qachon** yuklanmaydi. `DataBase.db`
faylini ham hech qachon qo'lda `git add` qilmang.

### 9.3 Railway'ga joylash (bosqichma-bosqich)

**Muhim narx eslatmasi:** Railway'da endi doimiy bepul tarif yo'q — yangi hisobga
30 kunlik yoki $5 gacha bo'lgan bir martalik sinov krediti beriladi, shundan keyin
kamida **Hobby ($5/oy)** tarifiga o'tish kerak bo'ladi. Kichik bot (baza + doimiy
ishlaydigan Python jarayoni) uchun oyiga taxminan $5-10 atrofida xarajat kutilsin.
Agar butunlay bepul variant kerak bo'lsa, Oracle Cloud Free Tier (doimiy bepul, lekin
sozlash birmuncha texnik) yoki boshqa VPS'ga o'tishni tavsiya qilaman — xohlasangiz shu
yo'l bo'yicha ham qadamlarni yozib beraman.

1. https://railway.app ga GitHub akkauntingiz bilan kiring (kredit karta so'ralishi mumkin,
   hozircha haqiqiy pul yechilmaydi).
2. **New Project → Deploy from GitHub repo** → `mpt-bot` repongizni tanlang.
3. Railway loyihani avtomatik aniqlaydi (`railway.json` va `requirements.txt` orqali).
4. **Variables** bo'limiga `.env.example` dagi barcha o'zgaruvchilarni kiriting:
   `BOT_TOKEN`, `ADMIN_IDS`, `OWNER_ID`, `CLICK_*`, `GEMINI_API_KEY` va h.k.
5. **Ma'lumotlar bazasi yo'qolib qolmasligi uchun Volume ulang** (muhim!):
   Railway loyihangizda **+ New → Volume** tugmasini bosing, mount path sifatida
   `/data` kiriting, so'ng **Variables** bo'limida `DB_PATH=/data/mpt_bot.db` qo'shing.
   Volume bo'lmasa, Railway konteynerni har safar qayta ishga tushirganda (deploy,
   restart) bazangiz **o'chib ketadi** — bu eng ko'p uchraydigan xato.
6. **Deploy** tugmasini bosing. Bir necha daqiqadan so'ng bot ishga tushadi (loglarni
   Railway paneli ichidan kuzatib turishingiz mumkin).
7. Botingizga `/start` yozib tekshiring, so'ng shaxsiy chatda `DataBase.db` faylini
   `/importdb` bilan yuboring (9.1-bo'lim).
8. Vaqti-vaqti bilan (masalan haftada bir) shaxsiy chatda `/backupdb` buyrug'ini
   yuborib, bazangizning zaxira nusxasini oling va xavfsiz joyda saqlang — Volume
   ishonchli bo'lsa-da, qo'shimcha zaxira hech qachon ortiqcha emas.

### 9.4 Keyingi safar kod yangilansa

```bash
git add .
git commit -m "Yangilanish tavsifi"
git push
```
Railway GitHub'ga ulangan bo'lgani uchun har bir `push`dan keyin **avtomatik qayta
deploy** qiladi — qo'shimcha amal talab qilinmaydi.

---

Savol tug'ilsa yoki keyingi bosqichlardan birini (masalan, to'liq pptx generatsiya,
Payme integratsiyasi, yoki webhook'ga o'tish) birga qilib ko'rishni xohlasangiz —
istalgan vaqtda ayting, shu loyiha ustida davom ettiraman.
