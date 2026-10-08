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
Shablon ichida quyidagi maxsus so'zlarni (placeholder) matn qutilariga yozsangiz,
ular avtomatik almashtiriladi:
    {{TOPIC}}        -> Taqdimot mavzusi
    {{FULLNAME}}     -> Talabaning ismi-familiyasi
    {{INSTITUTION}}  -> O'quv muassasasi
    {{DIRECTION}}    -> Yo'nalish/guruh
Masalan titul slaydda katta harflar bilan "{{TOPIC}}" deb yozing — bot buni
haqiqiy mavzu bilan almashtiradi, shrift/rang o'zgarmaydi.
============================================================

AI generatsiya qilingan har bir slaydga sarlavha va punktlar yangi matn qutilari
sifatida joylanadi; shu sababli rasm/freeform ko'rinishidagi shablonlarda ham
matn yozish mumkin. Shablonning o'zidagi dekorativ shakllar saqlanadi.
"""

import os
import random
import copy
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt

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


def _remove_slide(prs: Presentation, index: int):
    slide_id = prs.slides._sldIdLst[index]
    prs.part.drop_rel(slide_id.rId)
    prs.slides._sldIdLst.remove(slide_id)


def _add_textbox(slide, x: float, y: float, width: float, height: float, text: str, font_size: int, bold: bool = False):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(width), Inches(height))
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    frame.margin_left = Inches(0.08)
    frame.margin_right = Inches(0.08)
    frame.margin_top = Inches(0.04)
    frame.margin_bottom = Inches(0.04)
    paragraph = frame.paragraphs[0]
    paragraph.alignment = PP_ALIGN.CENTER if bold else PP_ALIGN.LEFT
    paragraph.text = text
    paragraph.font.name = "Arial"
    paragraph.font.size = Pt(font_size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = RGBColor(31, 41, 55)
    return shape


def _add_slide_text(slide, slide_data: dict, slide_number: int, total_slides: int, is_cover: bool):
    title_y = 1.25 if is_cover else 0.9
    title_height = 1.55 if is_cover else 1.1
    _add_textbox(
        slide, 2.2, title_y, 15.6, title_height,
        slide_data["title"].strip(), 34 if is_cover else 28, bold=True,
    )

    if is_cover:
        bullets = slide_data["bullets"][:2]
        body_y, body_height, font_size = 4.1, 2.5, 22
    else:
        bullets = slide_data["bullets"][:5]
        body_y, body_height, font_size = 2.65, 6.2, 22

    body_shape = slide.shapes.add_textbox(
        Inches(2.3), Inches(body_y), Inches(15.4), Inches(body_height),
    )
    frame = body_shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    frame.margin_left = Inches(0.12)
    frame.margin_right = Inches(0.12)
    frame.margin_top = Inches(0.08)
    frame.margin_bottom = Inches(0.08)
    for index, bullet in enumerate(bullets):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = f"• {bullet.strip()}"
        paragraph.level = 0
        paragraph.font.name = "Arial"
        paragraph.font.size = Pt(font_size)
        paragraph.font.color.rgb = RGBColor(45, 55, 72)
        paragraph.space_after = Pt(18)

    _add_textbox(
        slide, 17.2, 10.35, 1.5, 0.45,
        f"{slide_number}/{total_slides}", 12,
    )


def build_presentation(
    template_path: str,
    output_path: str,
    topic: str,
    full_name: str,
    institution: str,
    direction: str,
    total_pages: int,
    slides_content: list[dict],
    content_slide_index: int = 1,
) -> str:
    prs = Presentation(template_path)
    if total_pages < 1 or len(slides_content) != total_pages:
        raise ValueError("Taqdimot sahifalari soni matn sahifalari soniga mos kelmadi.")

    mapping = {
        "{{TOPIC}}": topic,
        "{{FULLNAME}}": full_name,
        "{{INSTITUTION}}": institution or "",
        "{{DIRECTION}}": direction or "",
    }

    if not prs.slides:
        raise ValueError("Tanlangan PowerPoint shablonida slayd yo'q.")

    while len(prs.slides) < total_pages:
        new_slide = _duplicate_slide(prs, content_slide_index)
        _replace_placeholders(new_slide, mapping)
    while len(prs.slides) > total_pages:
        _remove_slide(prs, len(prs.slides) - 1)

    for slide_number, slide in enumerate(prs.slides, start=1):
        _replace_placeholders(slide, mapping)
        _add_slide_text(
            slide, slides_content[slide_number - 1], slide_number, total_pages,
            is_cover=slide_number == 1,
        )
        if slide_number == 1 and (full_name or institution or direction):
            details = "  |  ".join(value for value in (full_name, institution, direction) if value)
            _add_textbox(slide, 2.5, 7.25, 15.0, 0.7, details, 16)

    prs.save(output_path)
    return output_path
