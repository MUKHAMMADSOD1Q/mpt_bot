import re

# Lotin va kirill harflarini qamrab oluvchi so'z: kamida 2 ta harf
_WORD_RE = re.compile(r"^[A-Za-zА-Яа-яЎўҚқҒғҲҳIʻʼ'`\-]+$", re.UNICODE)


def is_valid_topic(text: str) -> bool:
    text = text.strip()
    if len(text) < 2:
        return False
    if text.isdigit():
        return False
    return True


def is_valid_pages(text: str, min_pages: int, max_pages: int) -> tuple[bool, int | None]:
    text = text.strip()
    if not text.isdigit():
        return False, None
    value = int(text)
    if value < min_pages or value > max_pages:
        return False, None
    return True, value


def is_valid_full_name(text: str) -> bool:
    """Faqat so'zlardan iborat, raqamsiz, va har bir so'z kamida 2 ta harfdan iborat bo'lishi kerak."""
    text = text.strip()
    if not text:
        return False
    words = text.split()
    if not words:
        return False
    for w in words:
        if not _WORD_RE.match(w):
            return False
        if len(w) < 2:
            return False
    return True


def is_valid_optional_text(text: str) -> bool:
    """Ixtiyoriy maydonlar (o'quv joyi, yo'nalish) uchun: bo'sh bo'lishi mumkin,
    lekin to'ldirilsa raqam yoki yakka harflardan iborat bo'lmasligi kerak."""
    text = text.strip()
    if not text:
        return True
    if text.isdigit():
        return False
    words = text.split()
    for w in words:
        if len(w) < 2 and w.isalpha():
            return False
    return True
