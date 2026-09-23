"""
Tayyor shablon (.pptx) asosida taqdimot generatsiya qilish uchun boshlang'ich modul.

============================================================
SIZ QAYERGA VA QANDAY SHABLON YUKLAYSIZ?
============================================================
Papka: assets/templates/<tarif_kaliti>/  (masalan: assets/templates/standart/)
Har bir tarif uchun (bepul, start, standart, smart, pro, elite, maxsus) shu nomdagi
papka yarating va ichiga 10 tadan .pptx shablon joylang (nomi muhim emas, masalan
1.pptx, 2.pptx ... 10.pptx). Bot buyurtma kelganda shu tarif papkasidan TASODIFIY
bittasini tanlab, matn joylarini avtomatik to'ldiradi — foydalanuvchiga qaysi
shablon ishlatilgani haqida hech narsa ko'rsatilmaydi.

Shablon FORMATI — .pptx (PowerPoint), boshqa emas, chunki:
- python-pptx kutubxonasi orqali matn qutilarini DASTURIY ravishda, ya'ni
  formatni (shrift, rang, joylashuv) buzmasdan almashtirish mumkin;
- .pdf yoki Canva/Figma eksporti kabi formatlarda matnni qayta joylash amalda
  imkonsiz yoki juda mo'rt (rasm sifatida "yopishib qoladi").
Shablon ichida quyidagi maxsus so'zlarni (placeholder) matn qutilariga yozing —
ular avtomatik almashtiriladi:
    {{TOPIC}}        -> Taqdimot mavzusi
    {{FULLNAME}}     -> Talabaning ismi-familiyasi
    {{INSTITUTION}}  -> O'quv muassasasi
    {{DIRECTION}}    -> Yo'nalish/guruh
Masalan titul slaydda katta harflar bilan "{{TOPIC}}" deb yozing — bot buni
haqiqiy mavzu bilan almashtiradi, shrift/rang o'zgarmaydi.
============================================================
"""

import os
import random
import copy
from pptx import Presentation

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "templates")


def pick_random_template(tariff_key: str) -> str | None:
    """Berilgan tarif uchun assets/templates/<tariff_key>/ papkasidan tasodifiy
    bitta .pptx shablonni tanlaydi. Papka bo'sh yoki mavjud bo'lmasa None qaytaradi."""
    folder = os.path.join(TEMPLATES_DIR, tariff_key)
    if not os.path.isdir(folder):
        return None
    files = [f for f in os.listdir(folder) if f.lower().endswith(".pptx")]
    if not files:
        return None
    return os.path.join(folder, random.choice(files))


def _duplicate_slide(prs: Presentation, index: int):
    """prs ichidagi index-slaydni nusxalab, taqdimot oxiriga qo'shadi."""
    source = prs.slides[index]
    slide_layout = source.slide_layout
    new_slide = prs.slides.add_slide(slide_layout)

    # Bo'sh placeholderlarni tozalash
    for shape in list(new_slide.shapes):
        shape._element.getparent().remove(shape._element)

    # Manba slayddagi barcha shakllarni (matn, rasm va h.k.) nusxalash
    for shape in source.shapes:
        new_el = copy.deepcopy(shape._element)
        new_slide.shapes._spTree.append(new_el)

    return new_slide


def _replace_placeholders(slide, mapping: dict):
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        for paragraph in shape.text_frame.paragraphs:
            for run in paragraph.runs:
                for key, value in mapping.items():
                    if key in run.text:
                        run.text = run.text.replace(key, value)


def generate_slide_content(topic: str, slide_number: int, total_pages: int) -> str:
    """
    Bu yerga keyinchalik AI (masalan Claude API) chaqiruvini ulab,
    har bir slayd uchun sarlavha/matn generatsiya qilish mumkin.
    Hozircha oddiy namuna qaytaradi.
    """
    return f"{topic} — {slide_number}/{total_pages}-qism"


def build_presentation(
    template_path: str,
    output_path: str,
    topic: str,
    full_name: str,
    institution: str,
    direction: str,
    total_pages: int,
    content_slide_index: int = 1,
) -> str:
    prs = Presentation(template_path)

    mapping = {
        "{{TOPIC}}": topic,
        "{{FULLNAME}}": full_name,
        "{{INSTITUTION}}": institution or "",
        "{{DIRECTION}}": direction or "",
    }

    # Titul slayd (odatda 0-index) - placeholderlarni to'ldirish
    if len(prs.slides) > 0:
        _replace_placeholders(prs.slides[0], mapping)

    # Kerakli sahifa soniga yetguncha kontent slaydini ko'paytirish
    current_count = len(prs.slides)
    while current_count < total_pages:
        new_slide = _duplicate_slide(prs, content_slide_index)
        slide_num = current_count + 1
        _replace_placeholders(new_slide, mapping)
        # Namunaviy sarlavhani ham yangilash (agar {{TOPIC}} bo'lmasa)
        current_count += 1

    prs.save(output_path)
    return output_path
