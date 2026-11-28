import re
from decimal import Decimal, InvalidOperation


# Проверка корректности дозировки
def is_valid_dose(value):
    value = value.strip().replace(",", ".")

    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value):
        return False

    try:
        dose = Decimal(value)
    except InvalidOperation:
        return False

    return dose.is_finite() and dose > 0
