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
import math
import re
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_FILL
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


def presentation_filename(topic: str) -> str:
    words = []
    for word in topic.split():
        safe_word = re.sub(r"[^\w]+", "", word, flags=re.UNICODE)
        if safe_word:
            words.append(safe_word)
        if len(words) == 4:
            break
    return f"{'_'.join(words) or 'Taqdimot'}.pptx"


def _slide_text_color(slide) -> RGBColor:
    try:
        if slide.background.fill.type != MSO_FILL.SOLID:
            return RGBColor(31, 41, 55)
        rgb = slide.background.fill.fore_color.rgb
    except (AttributeError, TypeError, ValueError):
        return RGBColor(31, 41, 55)
    if not rgb:
        return RGBColor(31, 41, 55)

    color = str(rgb)
    if len(color) != 6:
        return RGBColor(31, 41, 55)
    red, green, blue = (int(color[i:i + 2], 16) for i in (0, 2, 4))
    luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255
    if luminance < 0.5:
        return RGBColor(248, 250, 252)
    return RGBColor(31, 41, 55)


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
    paragraph.font.color.rgb = _slide_text_color(slide)
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
        paragraph.font.color.rgb = _slide_text_color(slide)
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
    if total_pages < 3 or len(slides_content) != total_pages - 2:
        raise ValueError("Matn sahifalari soni umumiy taqdimot sahifalaridan 2 taga kam bo'lishi kerak.")

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

    cover = prs.slides[0]
    _replace_placeholders(cover, mapping)
    _add_textbox(
        cover, 2.2, 2.6, 15.6, 1.7, topic.strip(), 36, bold=True,
    )
    cover_details = [full_name.strip()]
    if institution.strip():
        cover_details.append(institution.strip())
    if direction.strip():
        cover_details.append(direction.strip())
    for index, detail in enumerate(cover_details):
        _add_textbox(
            cover, 2.5, 5.6 + index * 0.7, 15.0, 0.6, detail,
            20 if index == 0 else 16, bold=index == 0,
        )

    for slide_number, slide_data in enumerate(slides_content, start=2):
        slide = prs.slides[slide_number - 1]
        _replace_placeholders(slide, mapping)
        _add_slide_text(
            slide, slide_data, slide_number, total_pages, is_cover=False,
        )

    thank_you = prs.slides[-1]
    for shape in list(thank_you.shapes):
        shape._element.getparent().remove(shape._element)
    _add_textbox(
        thank_you, 2.2, 4.2, 15.6, 1.4, "RAHMAT!", 42, bold=True,
    )

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
    content_pages = len(paragraphs)
    if not content_pages:
        raise ValueError("Taqdimot uchun kamida bitta abzats kerak.")
    total_pages = content_pages + 2

    prs = Presentation(template_path)
    if len(prs.slides) < 2:
        raise ValueError("Tanlangan shablonda kontent slaydi topilmadi.")

    while len(prs.slides) < total_pages:
        _duplicate_slide(prs, 1)
    while len(prs.slides) > total_pages:
        _remove_slide(prs, len(prs.slides) - 1)

    width = prs.slide_width / 914400
    height = prs.slide_height / 914400
    cover = prs.slides[0]
    _add_textbox(
        cover,
        width * 0.08,
        height * 0.28,
        width * 0.84,
        height * 0.18,
        topic.strip(),
        36,
        bold=True,
    )
    cover_details = [full_name.strip()]
    if institution.strip():
        cover_details.append(institution.strip())
    if direction.strip():
        cover_details.append(direction.strip())
    details_y = height * 0.52
    for index, detail in enumerate(cover_details):
        _add_textbox(
            cover,
            width * 0.12,
            details_y + index * height * 0.075,
            width * 0.76,
            height * 0.065,
            detail,
            20 if index == 0 else 16,
            bold=index == 0,
        )

    images_by_page: dict[int, list[str]] = {}
    for index, image_path in enumerate(image_paths):
        page_index = min(content_pages - 1, index * content_pages // len(image_paths))
        images_by_page.setdefault(page_index, []).append(image_path)

    for page_index, paragraph_text in enumerate(paragraphs):
        slide = prs.slides[page_index + 1]
        page_images = images_by_page.get(page_index, [])
        body_height = height * 0.68
        body_y = height * 0.18
        text_width = width * (0.43 if page_images else 0.54)
        text_x = (
            width * (0.08 if page_index % 2 == 0 else 0.43)
            if page_images
            else (width - text_width) / 2
        )
        paragraph_shape = slide.shapes.add_textbox(
            Inches(text_x),
            Inches(body_y),
            Inches(text_width),
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
        paragraph.text = paragraph_text.strip()
        paragraph.alignment = PP_ALIGN.LEFT
        paragraph.font.name = "Arial"
        paragraph.font.size = Pt(26)
        paragraph.font.color.rgb = _slide_text_color(slide)

        if page_images:
            image_x = width * (0.58 if page_index % 2 == 0 else 0.08)
            image_y = body_y
            image_width = width * 0.31
            image_height = body_height
            columns = math.ceil(math.sqrt(len(page_images)))
            rows = math.ceil(len(page_images) / columns)
            cell_width = Inches(image_width / columns)
            cell_height = Inches(image_height / rows)
            for image_index, image_path in enumerate(page_images):
                column = image_index % columns
                row = image_index // columns
                picture = slide.shapes.add_picture(
                    image_path,
                    Inches(image_x + column * image_width / columns),
                    Inches(image_y + row * image_height / rows),
                )
                box_width = max(1, int(cell_width) - Inches(0.12))
                box_height = max(1, int(cell_height) - Inches(0.12))
                scale = min(box_width / picture.width, box_height / picture.height)
                picture.width = int(picture.width * scale)
                picture.height = int(picture.height * scale)
                picture.left = (
                    Inches(image_x + column * image_width / columns)
                    + int((cell_width - picture.width) / 2)
                )
                picture.top = (
                    Inches(image_y + row * image_height / rows)
                    + int((cell_height - picture.height) / 2)
                )

    thank_you = prs.slides[-1]
    for shape in list(thank_you.shapes):
        shape._element.getparent().remove(shape._element)
    _add_textbox(
        thank_you,
        width * 0.08,
        height * 0.38,
        width * 0.84,
        height * 0.24,
        "RAHMAT!",
        42,
        bold=True,
    )

    prs.save(output_path)
    return output_path
