"""Phone numbers are stored and compared in E.164 form (+16132462840)."""

import re

_E164 = re.compile(r"^\+[1-9]\d{7,14}$")


def normalize_phone(raw: str) -> str:
    """Strip formatting and return E.164, or raise ValueError.

    Accepts what people type — "+1 (613) 246-2840" — but requires the leading
    "+country code", since a bare national number is ambiguous.
    """
    cleaned = "+" + re.sub(r"\D", "", raw) if raw.strip().startswith("+") else re.sub(r"\D", "", raw)
    if not _E164.match(cleaned):
        raise ValueError("not a valid phone number")
    return cleaned
