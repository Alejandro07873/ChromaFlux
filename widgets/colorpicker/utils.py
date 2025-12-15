import re

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def is_valid_hex(text: str) -> bool:
    return bool(HEX_RE.match(text))
