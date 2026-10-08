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


def pick_random_template(tariff_key: str, allowed_files: tuple[str, ...] | None = None) -> str | None:
    """Berilgan tarif uchun assets/templates/<tariff_key>/ papkasidan tasodifiy
    bitta .pptx shablonni tanlaydi. Papka bo'sh yoki mavjud bo'lmasa None qaytaradi."""
    folder = os.path.join(TEMPLATES_DIR, tariff_key)
    if not os.path.isdir(folder):
        return None
    files = [f for f in os.listdir(folder) if f.lower().endswith(".pptx")]
    if allowed_files is not None:
        allowed = {name.lower() for name in allowed_files}
        files = [name for name in files if name.lower() in allowed]
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


def build_manual_presentation(
    template_path: str,
    output_path: str,
    topic: str,
    full_name: str,
    institution: str,
    direction: str,
    paragraphs: list[str],
    image_paths: list[str],
) -> str:
    total_pages = len(paragraphs)
    if not total_pages:
        raise ValueError("Taqdimot uchun kamida bitta abzats kerak.")
    if len(image_paths) > total_pages:
        raise ValueError("Har bir slaydga bittadan ortiq rasm joylab bo'lmaydi.")

    prs = Presentation(template_path)
    if len(prs.slides) < 2:
        raise ValueError("Tanlangan shablonda kontent slaydi topilmadi.")

    while len(prs.slides) < total_pages:
        _duplicate_slide(prs, 1)
    while len(prs.slides) > total_pages:
        _remove_slide(prs, len(prs.slides) - 1)

    width = prs.slide_width / 914400
    height = prs.slide_height / 914400
    margin_x = width * 0.12
    title_y = height * 0.08
    title_height = height * 0.11
    body_y = height * 0.23
    body_height = height * 0.65
    text_width = width * 0.76
    image_slide_indexes = {
        min(total_pages - 1, index * total_pages // len(image_paths))
        for index in range(len(image_paths))
    } if image_paths else set()
    image_by_slide = dict(zip(sorted(image_slide_indexes), image_paths))

    details = "  |  ".join(value for value in (full_name, institution, direction) if value)
    for slide_index, slide in enumerate(prs.slides):
        has_image = slide_index in image_by_slide
        current_text_width = width * 0.51 if has_image else text_width
        _add_textbox(
            slide,
            margin_x,
            title_y,
            width * 0.76,
            title_height,
            topic,
            28,
            bold=True,
        )
        paragraph_shape = slide.shapes.add_textbox(
            Inches(margin_x),
            Inches(body_y),
            Inches(current_text_width),
            Inches(body_height),
        )
        frame = paragraph_shape.text_frame
        frame.clear()
        frame.word_wrap = True
        frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        frame.margin_left = Inches(0.12)
        frame.margin_right = Inches(0.12)
        frame.margin_top = Inches(0.08)
        frame.margin_bottom = Inches(0.08)
        paragraph = frame.paragraphs[0]
        paragraph.text = paragraphs[slide_index].strip()
        paragraph.alignment = PP_ALIGN.LEFT
        paragraph.font.name = "Arial"
        paragraph.font.size = Pt(22)
        paragraph.font.color.rgb = RGBColor(45, 55, 72)

        if has_image:
            picture = slide.shapes.add_picture(
                image_by_slide[slide_index],
                Inches(width * 0.69),
                Inches(body_y + body_height * 0.17),
            )
            box_width = Inches(width * 0.25)
            box_height = Inches(body_height * 0.66)
            scale = min(box_width / picture.width, box_height / picture.height)
            picture.width = int(picture.width * scale)
            picture.height = int(picture.height * scale)
            picture.left = Inches(width * 0.69) + int((box_width - picture.width) / 2)
            picture.top = Inches(body_y + body_height * 0.17) + int((box_height - picture.height) / 2)

        if details and slide_index == 0:
            _add_textbox(
                slide,
                margin_x,
                height * 0.91,
                width * 0.76,
                height * 0.045,
                details,
                12,
            )
        _add_textbox(
            slide,
            width * 0.87,
            height * 0.92,
            width * 0.08,
            height * 0.04,
            f"{slide_index + 1}/{total_pages}",
            12,
        )

    prs.save(output_path)
    return output_path
