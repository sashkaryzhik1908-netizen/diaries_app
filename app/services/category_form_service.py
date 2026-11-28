from datetime import datetime

from sqlalchemy import select

from app.extensions import db
from app.models import VariableOption
from app.services.validators import is_valid_dose


# Обработка обычных категорий
def process_category_form(form, variables, category):
    values = {}
    errors = []

    # Обработка переменных категории
    for variable in variables:
        # Обработка множественного выбора
        if variable.field_type == "multiselect":
            raw_selected_ids = form.get(variable.name, "").split(",")

            # Проверка ID выбранных вариантов
            if any(
                option_id and not option_id.isdigit() for option_id in raw_selected_ids
            ):
                errors.append(
                    f"Выбраны некорректные варианты в поле «{variable.label}»."
                )
                values[variable.name] = ""
                continue

            selected_ids = [option_id for option_id in raw_selected_ids if option_id]

            # Проверка повторяющихся вариантов
            if len(selected_ids) != len(set(selected_ids)):
                errors.append(
                    f"В поле «{variable.label}» обнаружены повторяющиеся варианты."
                )
                values[variable.name] = ""
                continue

            # Получение выбранных вариантов из базы данных
            selected_options = db.session.scalars(
                select(VariableOption).where(
                    VariableOption.variable_id == variable.id,
                    VariableOption.id.in_(
                        [int(option_id) for option_id in selected_ids]
                    ),
                )
            ).all()

            options = {str(option.id): option for option in selected_options}

            # Проверка допустимости выбранных вариантов
            if len(options) != len(selected_ids):
                errors.append(
                    f"В поле «{variable.label}» выбраны недопустимые варианты."
                )

            # Обработка препаратов
            # Обработка препаратов
            if variable.name == "drug":
                drug_parts = []

                # Обработка дозировок выбранных препаратов
                for option_id in selected_ids:
                    option = options.get(option_id)

                    if not option:
                        continue

                    dose = form.get(
                        f"dose_{option_id}",
                        "",
                    ).strip()

                    if not dose:
                        errors.append(f"Укажите дозировку препарата «{option.value}».")
                        continue

                    # Проверка корректности дозировки
                    if not is_valid_dose(dose):
                        errors.append(
                            f"Дозировка препарата «{option.value}» должна быть положительным числом."
                        )
                        continue

                    drug_parts.append(f"{option.output_value} в дозе {dose} мкг/кг/мин")

                values[variable.name] = ", ".join(drug_parts)

            # Формирование значений остальных multiselect-полей
            else:
                values[variable.name] = ", ".join(
                    options[option_id].output_value
                    for option_id in selected_ids
                    if option_id in options
                )

            # Формирование списка синдромов
            if variable.name == "reasons":
                values["syndromes"] = [
                    options[option_id].value
                    for option_id in selected_ids
                    if option_id in options
                ]

        # Обработка одиночного выбора
        elif variable.field_type == "select":
            selected = form.get(
                variable.name,
                "",
            )

            option = next(
                (option for option in variable.options if option.value == selected),
                None,
            )

            # Проверка допустимости выбранного варианта
            if selected and not option:
                errors.append(f"Выбран недопустимый вариант в поле «{variable.label}».")

            values[variable.name] = option.output_value if option else ""

        # Обработка даты
        elif variable.field_type == "date":
            date_value = form.get(
                variable.name,
                "",
            ).strip()

            if date_value:
                try:
                    values[variable.name] = datetime.strptime(
                        date_value,
                        "%Y-%m-%d",
                    ).strftime("%d.%m.%Y")

                except ValueError:
                    errors.append(f"Укажите корректную дату в поле «{variable.label}».")
                    values[variable.name] = ""
            else:
                values[variable.name] = ""

        # Обработка текстовых и числовых полей
        else:
            values[variable.name] = form.get(
                variable.name,
                "",
            ).strip()

        # Проверка обязательных полей
        if variable.required and not values[variable.name] and variable.name != "dose":
            errors.append(f"Заполните поле «{variable.label}».")

    # Сброс старого общего поля дозировки
    if any(variable.name == "drug" for variable in variables):
        values["dose"] = ""

    # Обработка дополнительных жалоб
    if category.slug == "complaints":
        custom_complaints = form.get(
            "custom_complaints",
            "",
        ).strip()

        if custom_complaints:
            values["custom_complaints"] = f", {custom_complaints}"
        else:
            values["custom_complaints"] = ""

    return values, errors
