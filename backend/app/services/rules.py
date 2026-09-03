from __future__ import annotations


def zone_from_location(location: str) -> str:
    text = str(location or "").strip()
    if not text:
        return "SEM_LOCALIZACAO"
    return text.split(".", 1)[0].strip() if "." in text else text


def calculate_difference(counted: int, system_stock: int) -> int:
    return int(counted) - max(int(system_stock), 0)


def classify_difference(difference: int) -> str:
    if difference == 0:
        return "OK"
    return "SOBRA" if difference > 0 else "FALTA"
