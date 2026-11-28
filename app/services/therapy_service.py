import json

from sqlalchemy import select

from app.extensions import db
from app.models import Category, DiaryEntry, TherapyMedication, TherapyPurpose

# ___Цели терапии___


# Получение списка целей терапии
def get_therapy_purposes():
    return db.session.scalars(
        select(TherapyPurpose).order_by(TherapyPurpose.name)
    ).all()


# Проверка существования цели терапии
def get_existing_purpose(name, exclude_id=None):
    query = select(TherapyPurpose).where(TherapyPurpose.name == name)

    if exclude_id is not None:
        query = query.where(TherapyPurpose.id != exclude_id)

    return db.session.scalar(query)


# Добавление цели терапии
def create_therapy_purpose(name, output_value):
    purpose = TherapyPurpose(
        name=name,
        output_value=output_value,
    )

    db.session.add(purpose)
    db.session.commit()

    return purpose


# Редактирование цели терапии
def update_therapy_purpose(purpose, name, output_value):
    purpose.name = name
    purpose.output_value = output_value

    db.session.commit()

    return purpose


# Проверка использования справочника в назначениях
def _is_prescription_item_used(field_prefixes, item_id):
    entries = db.session.scalars(
        select(DiaryEntry.form_data)
        .join(Category, DiaryEntry.category_id == Category.id)
        .where(Category.slug == "prescriptions")
    )

    prefixes = tuple(f"{prefix}[" for prefix in field_prefixes)

    for raw_form_data in entries:
        try:
            form_data = json.loads(raw_form_data)
        except (json.JSONDecodeError, TypeError):
            # Не удаляем запись, если данные назначений повреждены
            return True

        if not isinstance(form_data, dict):
            return True

        for key, values in form_data.items():
            if key.startswith(prefixes) and key.endswith("]"):
                if not isinstance(values, list):
                    return True

                if str(item_id) in values:
                    return True

    return False


# Проверка использования цели терапии
def is_purpose_used(purpose_id):
    return _is_prescription_item_used(
        ("purpose_id",),
        purpose_id,
    )


# Удаление цели терапии
def delete_therapy_purpose(purpose):
    db.session.delete(purpose)
    db.session.commit()


# ___Препараты___


# Получение списка препаратов
def get_therapy_medications(purpose_id):
    return db.session.scalars(
        select(TherapyMedication)
        .join(TherapyMedication.purposes)
        .where(TherapyPurpose.id == purpose_id)
        .order_by(TherapyMedication.name)
    ).all()


# Получение полного списка препаратов
def get_all_therapy_medications():
    return db.session.scalars(
        select(TherapyMedication).order_by(TherapyMedication.name)
    ).all()


# Проверка существования препарата
def get_existing_medication(name, exclude_id=None):
    query = select(TherapyMedication).where(TherapyMedication.name == name)

    if exclude_id is not None:
        query = query.where(TherapyMedication.id != exclude_id)

    return db.session.scalar(query)


# Проверка идентификаторов целей терапии
def validate_purpose_ids(raw_purpose_ids):
    try:
        purpose_ids = [
            int(purpose_id)
            for purpose_id in raw_purpose_ids.split(",")
            if purpose_id.strip()
        ]
    except ValueError:
        return [], "Некорректные идентификаторы целей терапии."

    if len(purpose_ids) != len(set(purpose_ids)):
        return [], "Цели терапии не должны повторяться."

    existing_ids = set(
        db.session.scalars(
            select(TherapyPurpose.id).where(TherapyPurpose.id.in_(purpose_ids))
        ).all()
    )

    if set(purpose_ids) != existing_ids:
        return [], "Выбраны несуществующие цели терапии."

    return purpose_ids, None


# Добавление препарата
def create_therapy_medication(name, purpose_ids):
    purposes = db.session.scalars(
        select(TherapyPurpose).where(TherapyPurpose.id.in_(purpose_ids))
    ).all()

    medication = TherapyMedication(name=name, purposes=purposes)

    db.session.add(medication)
    db.session.commit()

    return medication


# Редактирование препарата
def update_therapy_medication(medication, name, purpose_ids):
    purposes = db.session.scalars(
        select(TherapyPurpose).where(TherapyPurpose.id.in_(purpose_ids))
    ).all()

    medication.name = name
    medication.purposes = purposes

    db.session.commit()

    return medication


# Проверка использования препарата
def is_medication_used(medication_id):
    return _is_prescription_item_used(
        ("medication_id", "additional_medication_id"),
        medication_id,
    )


# Удаление препарата
def delete_therapy_medication(medication):
    db.session.delete(medication)
    db.session.commit()
