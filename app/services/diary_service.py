import json
from datetime import UTC
from zoneinfo import ZoneInfo

from flask import current_app
from sqlalchemy import func, select

from app.extensions import db
from app.models import (
    Category,
    Diary,
    DiaryEntry,
    TemplateVariable,
    TherapyMedication,
    TherapyPurpose,
    TherapySource,
    TherapySourceValue,
)

LOCAL_TIMEZONE = ZoneInfo("Asia/Almaty")


# Время
def to_local_time(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(LOCAL_TIMEZONE)


# Получение дневника пользователя
def get_diary_for_user(diary_id, user_id):
    return db.first_or_404(
        select(Diary).where(
            Diary.id == diary_id,
            Diary.user_id == user_id,
        )
    )


# Получение записи дневника по категории
def get_diary_entry(diary_id, category_id):
    return db.session.scalar(
        select(DiaryEntry).where(
            DiaryEntry.diary_id == diary_id,
            DiaryEntry.category_id == category_id,
        )
    )


# Получение категории
def get_category(category_id):
    return db.get_or_404(Category, category_id)


# Получение переменных шаблона категории
def get_category_variables(category_id):
    return db.session.scalars(
        select(TemplateVariable)
        .where(TemplateVariable.category_id == category_id)
        .order_by(TemplateVariable.order)
    ).all()


# Получение целей терапии
def get_therapy_purposes():
    return db.session.scalars(
        select(TherapyPurpose).order_by(TherapyPurpose.name)
    ).all()


# Получение препаратов
def get_therapy_medications():
    return db.session.scalars(
        select(TherapyMedication).order_by(TherapyMedication.name)
    ).all()


# Получение группы дополнительных параметров терапии
def get_therapy_sources():
    sources = db.session.scalars(select(TherapySource)).all()

    return {source.name: source for source in sources}


# Получение значений дополнительных параметров терапии
def get_therapy_source_values():
    return db.session.scalars(
        select(TherapySourceValue).order_by(TherapySourceValue.id)
    ).all()


# Генерация текста категории
def generate_category_text(category, values):
    return current_app.jinja_env.from_string(category.template).render(**values)


# Получение последней позиции записи дневника
def get_last_entry_position(diary_id):
    position = db.session.scalar(
        select(func.max(DiaryEntry.position)).where(DiaryEntry.diary_id == diary_id)
    )
    return position if position is not None else -1


# Создание записи дневника
def create_diary_entry(
    diary_id,
    category_id,
    generated_text,
    syndromes,
    form_data,
):
    last_position = get_last_entry_position(diary_id)

    entry = DiaryEntry(
        diary_id=diary_id,
        category_id=category_id,
        text=generated_text,
        position=last_position + 1,
        syndromes=syndromes,
        form_data=json.dumps(form_data, ensure_ascii=False),
    )

    db.session.add(entry)

    return entry


# Обновление записи дневника
def update_diary_entry(entry, generated_text, syndromes, form_data):
    entry.text = generated_text
    entry.syndromes = syndromes
    entry.form_data = json.dumps(form_data, ensure_ascii=False)

    return entry


# Сохранение записи дневника
def save_diary_entry():
    db.session.commit()
