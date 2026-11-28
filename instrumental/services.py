import re
from collections import defaultdict
from datetime import datetime

from sqlalchemy import select

from app.extensions import db
from instrumental.models import (
    InstrumentalAlias,
    InstrumentalIndicator,
    InstrumentalSource,
)


def create_instrumental_indicator(name):
    """Создаёт инструментальный метод."""
    indicator = InstrumentalIndicator(
        name=name,
    )

    db.session.add(indicator)
    db.session.commit()

    return indicator


def update_instrumental_indicator(
    indicator,
    name,
):
    """Изменяет инструментальный метод."""
    indicator.name = name

    db.session.commit()


def delete_instrumental_indicator(indicator):
    """Удаляет инструментальный метод."""
    db.session.delete(indicator)
    db.session.commit()


def get_indicator_aliases(indicator_id):
    """Получает альтернативные названия инструментального метода."""
    return db.session.scalars(
        select(InstrumentalAlias)
        .where(InstrumentalAlias.indicator_id == indicator_id)
        .order_by(InstrumentalAlias.alias)
    ).all()


def create_instrumental_alias(indicator_id, alias_text):
    """Создаёт альтернативное название инструментального метода."""
    alias = InstrumentalAlias(
        indicator_id=indicator_id,
        alias=alias_text,
    )

    db.session.add(alias)
    db.session.commit()

    return alias


def update_instrumental_alias(alias, indicator_id, alias_text):
    """Изменяет альтернативное название инструментального метода."""
    alias.indicator_id = indicator_id
    alias.alias = alias_text

    db.session.commit()


def delete_instrumental_alias(alias):
    """Удаляет альтернативное название инструментального метода."""
    db.session.delete(alias)
    db.session.commit()


def save_instrumental_source(diary_id, source, source_text, result_text):
    """Сохраняет исходный и обработанный текст."""
    if source is None:
        source = InstrumentalSource(
            diary_id=diary_id,
            source_text=source_text,
            result_text=result_text,
        )

        db.session.add(source)

    else:
        source.source_text = source_text
        source.result_text = result_text

    db.session.commit()

    return source


def generate_instrumental_text(source_text):
    """Формирует обработанный текст инструментальных исследований."""
    if not source_text:
        return ""

    indicators = db.session.scalars(select(InstrumentalIndicator)).all()

    # Словарь названий и алиасов.
    names = {}

    for indicator in indicators:
        names[indicator.name] = indicator.name

        for alias in indicator.aliases:
            names[alias.alias] = indicator.name

    def normalize_text(text):
        text = text.casefold().replace("ё", "е")
        text = text.replace("\u200b", "")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    normalized_names = {
        normalize_text(name): canonical for name, canonical in names.items()
    }

    # Разделение исходного текста на блоки по заголовкам исследований.
    headers = list(
        re.finditer(
            r"(?m)^\s*(?:\*\*)?(.+?\(\d{2}\.\d{2}\.\d{4}(?:\s+\d{2}:\d{2})?\))(?:\*\*)?\s*$",
            source_text,
        )
    )

    results = defaultdict(list)

    for index, header in enumerate(headers):
        title = header.group(1).strip()

        end = (
            headers[index + 1].start() if index + 1 < len(headers) else len(source_text)
        )

        block = source_text[header.end() : end].strip()

        # Извлечение даты.
        date_match = re.search(
            r"\((\d{2}\.\d{2}\.\d{4})(?:\s+\d{2}:\d{2})?\)",
            title,
        )

        date = date_match.group(1) if date_match else ""

        # Удаление даты и времени из названия исследования.
        study_name = re.sub(
            r"\s*\(\d{2}\.\d{2}\.\d{4}(?:\s+\d{2}:\d{2})?\)",
            "",
            title,
        ).strip()

        # Поиск исследования по справочнику или алиасу.
        canonical_name = normalized_names.get(
            normalize_text(study_name),
            study_name,
        )

        # Извлечение заключения.
        conclusion_match = re.search(
            r"Заключение\s*:\s*(.*)",
            block,
            flags=re.IGNORECASE | re.DOTALL,
        )

        conclusion = conclusion_match.group(1) if conclusion_match else block

        conclusion = conclusion.strip()

        # Удаление повторного префикса «Заключение:».
        # Удаление врача из конца заключения.
        # Удаление врача из конца заключения.
        conclusion = re.sub(
            r"\b(?:Врач|Вр\.)\s*:?\s*.*$",
            "",
            conclusion,
            flags=re.IGNORECASE,
        ).strip()

        if not conclusion:
            continue

        # Сбор одинаковых исследований в группы.
        results[canonical_name].append(
            {
                "date": date,
                "conclusion": conclusion,
            }
        )

    # Формирование итогового текста.
    output = []

    for study_name, entries in results.items():
        entries.sort(
            key=lambda item: (
                datetime.strptime(item["date"], "%d.%m.%Y")
                if item["date"]
                else datetime.max
            )
        )

        group = []

        for entry in entries:
            if entry["date"]:
                line = (
                    f"По данным {study_name} от {entry['date']}: {entry['conclusion']}"
                )
            else:
                line = f"По данным {study_name}: {entry['conclusion']}"

            group.append(line)

        output.append("\n".join(group))

    return "\n\n".join(output)
