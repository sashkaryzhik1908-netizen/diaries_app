import re
from decimal import Decimal, InvalidOperation

from sqlalchemy import select

from app.extensions import db
from laboratory.models import LaboratoryIndicator

DATE_PATTERN = re.compile(
    r"Дата завершения заказа:\s*(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2})"
)

VALUE_PATTERN = re.compile(r"^(?P<value>[<>≤≥]?\s*-?\d+(?:[.,]\d+)?)\s*(?P<unit>.*)$")

# Коды показателей ручной лейкоформулы.
# Их алиасы-коды не используем, чтобы не захватить автоматическую формулу.
MANUAL_DIFF_CODES = {
    "LYM",
    "MON",
    "META",
    "MYELO",
    "BAND",
    "SEG",
}


def normalize_text(value):
    """Нормализует текст для поиска показателей."""

    value = value.casefold().replace("ё", "е")
    return re.sub(r"\s+", " ", value).strip()


def parse_value(raw_value):
    """Разбирает значение и единицу измерения."""

    raw_value = raw_value.strip()

    match = VALUE_PATTERN.match(raw_value)

    if match:
        return {
            "value": match.group("value").strip(),
            "unit": match.group("unit").strip(),
        }

    return {
        "value": raw_value,
        "unit": "",
    }


def find_indicator(raw_name, indicators):
    """Ищет показатель в справочнике по названию или алиасу."""

    matches = []

    for indicator in indicators:
        aliases = [
            indicator.name,
            *[alias.alias for alias in indicator.aliases],
        ]

        if indicator.category.slug == "cbc" and indicator.code in MANUAL_DIFF_CODES:
            aliases = [
                alias
                for alias in aliases
                if normalize_text(alias) != normalize_text(indicator.code)
            ]

        for alias in aliases:
            alias = alias.strip()

            if not alias:
                continue

            pattern_text = re.escape(alias)

            # Допускаем пробелы и дефис между частями обозначения.
            pattern_text = pattern_text.replace(
                r"\ ",
                r"\s*[-–]?\s*",
            )

            pattern = re.compile(
                rf"(?<!\w){pattern_text}(?!\w)",
                re.IGNORECASE,
            )

            for match in pattern.finditer(raw_name):
                matches.append(
                    (
                        len(alias),
                        match.start(),
                        match.end(),
                        indicator,
                    )
                )

    if not matches:
        return None, raw_name

    # Выбираем наиболее длинное совпадение.
    # При одинаковой длине предпочитаем последнее вхождение:
    # оно обычно относится к названию самого показателя,
    # а не к названию исследования.
    matches.sort(
        key=lambda item: (item[0], item[1]),
        reverse=True,
    )

    _, start, _, indicator = matches[0]

    return indicator, raw_name[start:].strip()


def parse_indicator(raw_text, indicators, datetime):
    """Разбирает один показатель и сопоставляет его со справочником."""

    if " - " not in raw_text:
        return None

    # Для бактериологических исследований сохраняем
    # микроорганизм вместе с антибиотикограммой.
    if "вид микроорганизма" in normalize_text(raw_text):
        raw_name, raw_value = raw_text.split(" - ", 1)
    else:
        raw_name, raw_value = raw_text.rsplit(" - ", 1)

    raw_name = raw_name.strip()
    raw_value = raw_value.strip()

    # Исключаем показатели мочи.
    if "в моче" in normalize_text(raw_name):
        return None

    if not raw_name or not raw_value:
        return None

    indicator, matched_name = find_indicator(
        raw_name,
        indicators,
    )

    if indicator is None:
        return None

    # Автоматическую лейкоформулу не используем.
    # Ручные лимфоциты и моноциты распознаются по названиям,
    # а не по кодам LYM и MON.

    parsed_value = parse_value(raw_value)

    return {
        "datetime": datetime,
        "category": indicator.category.slug,
        "indicator_id": indicator.id,
        "indicator": indicator.name,
        "code": indicator.code,
        "raw_name": matched_name,
        "value": parsed_value["value"],
        "unit": parsed_value["unit"],
    }


def parse_laboratory_text(source_text):
    """Разбирает исходный текст лабораторных исследований."""
    source_text = source_text.replace("\u200b", "")
    source_text = source_text.replace("\ufeff", "")

    indicators = db.session.scalars(
        select(LaboratoryIndicator).join(LaboratoryIndicator.category)
    ).all()

    results = []
    date_matches = list(DATE_PATTERN.finditer(source_text))

    for index, date_match in enumerate(date_matches):
        datetime = date_match.group(1)
        start = date_match.end()

        if index + 1 < len(date_matches):
            end = date_matches[index + 1].start()
        else:
            end = len(source_text)

        order_text = source_text[start:end]

        for item in order_text.split(";"):
            item = item.strip()

            if not item or item.startswith("Примечание:"):
                continue

            result = parse_indicator(
                raw_text=item,
                indicators=indicators,
                datetime=datetime,
            )

            if result is not None:
                results.append(result)

    unique_results = []
    seen = set()

    for result in results:
        try:
            value = Decimal(result["value"].replace(",", "."))
        except InvalidOperation:
            value = result["value"]

        key = (
            result["datetime"],
            result["indicator_id"],
            value,
            result["unit"],
        )

        if key not in seen:
            seen.add(key)
            unique_results.append(result)

    return unique_results
