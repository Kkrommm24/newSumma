import re


def is_mostly_uppercase(text: str, min_len: int = 30) -> bool:
    if not text or len(text) < min_len:
        return False
    alpha_chars = ''.join(filter(str.isalpha, text))
    if not alpha_chars:
        return False
    # Kiểm tra xem có bất kỳ ký tự chữ thường nào không
    return not any(c.islower() for c in alpha_chars)


def contains_numbered_list(text: str) -> bool:
    return bool(re.search(r'^\s*\d+\.\s+', text, re.MULTILINE))
