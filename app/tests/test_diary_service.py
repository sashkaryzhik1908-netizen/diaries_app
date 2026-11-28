from werkzeug.datastructures import MultiDict

from app.extensions import db
from app.models import (
    Category,
    TemplateVariable,
    TherapyMedication,
    TherapyPurpose,
    VariableOption,
)
from app.services.category_form_service import process_category_form
from app.services.prescriptions_service import process_prescriptions


# Проверка обработки обычного текстового поля
def test_process_text_field(app):
    with app.app_context():
        category = Category(
            name="Жалобы",
            slug="complaints",
            template="Жалобы: {{ complaints }}",
        )

        variable = TemplateVariable(
            category_id=1,
            name="complaints",
            label="Жалобы",
            field_type="text",
            required=True,
        )

        form = MultiDict(
            {
                "complaints": "Головная боль",
            }
        )

        values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert values["complaints"] == "Головная боль"
        assert errors == []


# Проверка обязательного поля
def test_process_required_field(app):
    with app.app_context():
        category = Category(
            name="Жалобы",
            slug="complaints",
            template="Жалобы: {{ complaints }}",
        )

        variable = TemplateVariable(
            category_id=1,
            name="complaints",
            label="Жалобы",
            field_type="text",
            required=True,
        )

        form = MultiDict(
            {
                "complaints": "",
            }
        )

        values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert values["complaints"] == ""
        assert errors


# Проверка обработки даты
def test_process_date_field(app):
    with app.app_context():
        category = Category(
            name="Состояние",
            slug="condition",
            template="Дата: {{ date }}",
        )

        variable = TemplateVariable(
            category_id=1,
            name="date",
            label="Дата",
            field_type="date",
            required=False,
        )

        form = MultiDict(
            {
                "date": "2026-11-16",
            }
        )

        values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert values["date"] == "16.11.2026"
        assert errors == []


# Проверка некорректной даты
def test_process_invalid_date(app):
    with app.app_context():
        category = Category(
            name="Состояние",
            slug="condition",
            template="Дата: {{ date }}",
        )

        variable = TemplateVariable(
            category_id=1,
            name="date",
            label="Дата",
            field_type="date",
            required=False,
        )

        form = MultiDict(
            {
                "date": "неправильная дата",
            }
        )

        values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert values["date"] == ""
        assert errors


# Проверка выбора одного варианта
def test_process_select_field(app):
    with app.app_context():
        category = Category(
            name="Сознание",
            slug="consciousness",
            template="Сознание: {{ consciousness }}",
        )

        variable = TemplateVariable(
            category_id=1,
            name="consciousness",
            label="Сознание",
            field_type="select",
            required=True,
        )

        option = VariableOption(
            variable_id=1,
            value="Ясное",
            output_value="Сознание ясное",
        )

        variable.options.append(option)

        form = MultiDict(
            {
                "consciousness": "Ясное",
            }
        )

        values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert values["consciousness"] == "Сознание ясное"
        assert errors == []


# Проверка некорректного варианта
def test_process_invalid_select_field(app):
    with app.app_context():
        category = Category(
            name="Сознание",
            slug="consciousness",
            template="Сознание: {{ consciousness }}",
        )

        variable = TemplateVariable(
            category_id=1,
            name="consciousness",
            label="Сознание",
            field_type="select",
            required=True,
        )

        option = VariableOption(
            variable_id=1,
            value="Ясное",
            output_value="Сознание ясное",
        )

        variable.options.append(option)

        form = MultiDict(
            {
                "consciousness": "Несуществующий вариант",
            }
        )

        values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert values["consciousness"] == ""
        assert errors


# Проверка некорректного ID в multiselect
def test_process_invalid_multiselect_id(app):
    with app.app_context():
        category = Category(
            name="Состояние",
            slug="condition",
            template="Состояние",
        )

        variable = TemplateVariable(
            category_id=1,
            name="reasons",
            label="Причины",
            field_type="multiselect",
            required=False,
        )

        form = MultiDict(
            {
                "reasons": "abc",
            }
        )

        _values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert errors


# Проверка повторяющихся ID в multiselect
def test_process_duplicate_multiselect_ids(app):
    with app.app_context():
        category = Category(
            name="Состояние",
            slug="condition",
            template="Состояние",
        )

        variable = TemplateVariable(
            category_id=1,
            name="reasons",
            label="Причины",
            field_type="multiselect",
            required=False,
        )

        form = MultiDict(
            {
                "reasons": "1,1",
            }
        )

        _values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert errors


# Проверка формирования текста назначений
def test_process_prescriptions(app):
    with app.app_context():
        purpose = TherapyPurpose(
            name="Антибактериальная терапия",
            output_value="Антибактериальная терапия",
        )

        medication = TherapyMedication(
            name="Препарат",
            purposes=[purpose],
        )

        db_objects = [purpose, medication]

        db.session.add_all(db_objects)
        db.session.commit()

        form = MultiDict(
            {
                "purpose_id[0]": str(purpose.id),
                "medication_id[0][]": [str(medication.id)],
                "dose[0][]": ["100"],
                "unit[0][]": ["мг"],
                "administration_method[0]": "внутривенно",
                "frequency[0]": "2 р/сут",
                "start_date[0]": "2026-11-16",
            }
        )

        generated_text, errors = process_prescriptions(form)

        assert errors == []
        assert generated_text is not None
        assert "Препарат 100 мг" in generated_text
        assert "внутривенно" in generated_text
        assert "2 р/сут" in generated_text
        assert "с 16.11.2026" in generated_text


# Проверка обработки препаратов в multiselect
def test_process_category_form_drug(app):
    with app.app_context():
        category = Category(
            name="Терапия",
            slug="therapy",
            order=1,
            template="",
        )
        db.session.add(category)
        db.session.commit()

        variable = TemplateVariable(
            category_id=category.id,
            name="drug",
            label="Препараты",
            field_type="multiselect",
            required=True,
        )
        db.session.add(variable)
        db.session.commit()

        option = VariableOption(
            variable_id=variable.id,
            value="Норадреналин",
            output_value="норадреналин",
        )
        db.session.add(option)
        db.session.commit()

        form = MultiDict(
            [
                ("drug", str(option.id)),
                (f"dose_{option.id}", "0.5"),
            ]
        )

        values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert not errors
        assert values["drug"] == "норадреналин в дозе 0.5 мкг/кг/мин"
        assert values["dose"] == ""


# Проверка отсутствия дозировки препарата
def test_process_category_form_drug_without_dose(app):
    with app.app_context():
        category = Category(
            name="Терапия",
            slug="therapy",
            order=1,
            template="",
        )
        db.session.add(category)
        db.session.commit()

        variable = TemplateVariable(
            category_id=category.id,
            name="drug",
            label="Препараты",
            field_type="multiselect",
            required=True,
        )
        db.session.add(variable)
        db.session.commit()

        option = VariableOption(
            variable_id=variable.id,
            value="Норадреналин",
            output_value="норадреналин",
        )
        db.session.add(option)
        db.session.commit()

        form = MultiDict(
            [
                ("drug", str(option.id)),
                (f"dose_{option.id}", ""),
            ]
        )

        values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert any("Укажите дозировку" in error for error in errors)
        assert values["drug"] == ""


# Проверка формирования списка синдромов
def test_process_category_form_reasons(app):
    with app.app_context():
        category = Category(
            name="Причины",
            slug="reasons",
            order=1,
            template="",
        )
        db.session.add(category)
        db.session.commit()

        variable = TemplateVariable(
            category_id=category.id,
            name="reasons",
            label="Причины",
            field_type="multiselect",
            required=False,
        )
        db.session.add(variable)
        db.session.commit()

        option = VariableOption(
            variable_id=variable.id,
            value="Гнойно-воспалительный синдром",
            output_value="гнойно-воспалительным синдромом",
        )
        db.session.add(option)
        db.session.commit()

        form = MultiDict(
            [
                ("reasons", str(option.id)),
            ]
        )

        values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert not errors
        assert values["reasons"] == "гнойно-воспалительным синдромом"
        assert values["syndromes"] == ["Гнойно-воспалительный синдром"]


# Проверка недопустимого ID варианта multiselect
def test_process_category_form_multiselect_foreign_option(app):
    with app.app_context():
        category = Category(
            name="Причины",
            slug="reasons",
            order=1,
            template="",
        )
        db.session.add(category)
        db.session.commit()

        variable = TemplateVariable(
            category_id=category.id,
            name="reasons",
            label="Причины",
            field_type="multiselect",
            required=False,
        )
        db.session.add(variable)
        db.session.commit()

        form = MultiDict(
            [
                ("reasons", "999999"),
            ]
        )

        _values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert any("недопустимые варианты" in error for error in errors)


# Проверка пустого обязательного select
def test_process_category_form_required_empty_select(app):
    with app.app_context():
        category = Category(
            name="Состояние",
            slug="condition",
            order=1,
            template="",
        )
        db.session.add(category)
        db.session.commit()

        variable = TemplateVariable(
            category_id=category.id,
            name="condition",
            label="Состояние",
            field_type="select",
            required=True,
        )
        db.session.add(variable)
        db.session.commit()

        form = MultiDict(
            [
                ("condition", ""),
            ]
        )

        values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert values["condition"] == ""
        assert any("Заполните поле" in error for error in errors)


# Проверка дополнительного текста жалоб
def test_process_category_form_custom_complaints(app):
    with app.app_context():
        category = Category(
            name="Жалобы",
            slug="complaints",
            order=1,
            template="",
        )
        db.session.add(category)
        db.session.commit()

        form = MultiDict(
            [
                ("custom_complaints", "Боль в области живота"),
            ]
        )

        values, errors = process_category_form(
            form,
            [],
            category,
        )

        assert not errors
        assert values["custom_complaints"] == ", Боль в области живота"


# Проверка пустого дополнительного текста жалоб
def test_process_category_form_empty_custom_complaints(app):
    with app.app_context():
        category = Category(
            name="Жалобы",
            slug="complaints",
            order=1,
            template="",
        )
        db.session.add(category)
        db.session.commit()

        form = MultiDict(
            [
                ("custom_complaints", ""),
            ]
        )

        values, errors = process_category_form(
            form,
            [],
            category,
        )

        assert not errors
        assert values["custom_complaints"] == ""


# Проверка отсутствия групп назначений
def test_process_prescriptions_without_groups(app):
    with app.app_context():
        generated_text, errors = process_prescriptions(MultiDict())

        assert generated_text is None
        assert "Добавьте хотя бы одно назначение." in errors


# Проверка некорректной цели терапии
def test_process_prescriptions_invalid_purpose(app):
    with app.app_context():
        form = MultiDict(
            [
                ("purpose_id[0]", "999999"),
            ]
        )

        generated_text, errors = process_prescriptions(form)

        assert generated_text is None
        assert "Выберите корректную цель терапии." in errors


# Проверка отсутствия препаратов
def test_process_prescriptions_without_medications(app):
    with app.app_context():
        purpose = TherapyPurpose(
            name="Антибактериальная терапия",
            output_value="Антибактериальная терапия",
        )
        db.session.add(purpose)
        db.session.commit()

        form = MultiDict(
            [
                ("purpose_id[0]", str(purpose.id)),
            ]
        )

        generated_text, errors = process_prescriptions(form)

        assert generated_text is None
        assert "Добавьте хотя бы один препарат." in errors


# Проверка несовпадения количества препаратов и дозировок
def test_process_prescriptions_different_medications_and_doses(app):
    with app.app_context():
        purpose = TherapyPurpose(
            name="Терапия",
            output_value="Терапия",
        )
        medication = TherapyMedication(
            name="Цефтриаксон",
            purposes=[purpose],
        )
        db.session.add_all([purpose, medication])
        db.session.commit()

        form = MultiDict(
            [
                ("purpose_id[0]", str(purpose.id)),
                ("medication_id[0][]", str(medication.id)),
                ("medication_id[0][]", str(medication.id)),
                ("dose[0][]", "1"),
                ("unit[0][]", "гр"),
                ("unit[0][]", "гр"),
            ]
        )

        generated_text, errors = process_prescriptions(form)

        assert generated_text is None
        assert (
            "Количество препаратов, дозировок и единиц измерения не совпадает."
            in errors
        )


# Проверка некорректного препарата
def test_process_prescriptions_invalid_medication(app):
    with app.app_context():
        purpose = TherapyPurpose(
            name="Терапия",
            output_value="Терапия",
        )
        db.session.add(purpose)
        db.session.commit()

        form = MultiDict(
            [
                ("purpose_id[0]", str(purpose.id)),
                ("medication_id[0][]", "999999"),
                ("dose[0][]", "1"),
                ("unit[0][]", "гр"),
            ]
        )

        generated_text, errors = process_prescriptions(form)

        assert generated_text is None
        assert "Выберите корректный препарат." in errors


# Проверка пустой дозировки
def test_process_prescriptions_empty_dose(app):
    with app.app_context():
        purpose = TherapyPurpose(
            name="Терапия",
            output_value="Терапия",
        )
        medication = TherapyMedication(
            name="Цефтриаксон",
            purposes=[purpose],
        )
        db.session.add_all([purpose, medication])
        db.session.commit()

        form = MultiDict(
            [
                ("purpose_id[0]", str(purpose.id)),
                ("medication_id[0][]", str(medication.id)),
                ("dose[0][]", " "),
                ("unit[0][]", "гр"),
            ]
        )

        generated_text, errors = process_prescriptions(form)

        assert generated_text is None
        assert "Укажите дозу каждого препарата." in errors


# Проверка некорректного способа введения
def test_process_prescriptions_invalid_method(app):
    with app.app_context():
        purpose = TherapyPurpose(
            name="Терапия",
            output_value="Терапия",
        )
        medication = TherapyMedication(
            name="Цефтриаксон",
            purposes=[purpose],
        )
        db.session.add_all([purpose, medication])
        db.session.commit()

        form = MultiDict(
            [
                ("purpose_id[0]", str(purpose.id)),
                ("medication_id[0][]", str(medication.id)),
                ("dose[0][]", "1"),
                ("unit[0][]", "гр"),
                ("administration_method[0]", "неизвестный способ"),
                ("frequency[0]", "1 р/д"),
            ]
        )

        generated_text, errors = process_prescriptions(form)

        assert generated_text is None
        assert "Выберите корректный способ введения." in errors


# Проверка некорректной кратности
def test_process_prescriptions_invalid_frequency(app):
    with app.app_context():
        purpose = TherapyPurpose(
            name="Терапия",
            output_value="Терапия",
        )
        medication = TherapyMedication(
            name="Цефтриаксон",
            purposes=[purpose],
        )
        db.session.add_all([purpose, medication])
        db.session.commit()

        form = MultiDict(
            [
                ("purpose_id[0]", str(purpose.id)),
                ("medication_id[0][]", str(medication.id)),
                ("dose[0][]", "1"),
                ("unit[0][]", "гр"),
                ("administration_method[0]", "внутривенно"),
                ("frequency[0]", "каждый час"),
            ]
        )

        generated_text, errors = process_prescriptions(form)

        assert generated_text is None
        assert "Выберите корректную кратность." in errors


# Проверка некорректной даты начала назначения
def test_process_prescriptions_invalid_date(app):
    with app.app_context():
        purpose = TherapyPurpose(
            name="Терапия",
            output_value="Терапия",
        )
        medication = TherapyMedication(
            name="Цефтриаксон",
            purposes=[purpose],
        )
        db.session.add_all([purpose, medication])
        db.session.commit()

        form = MultiDict(
            [
                ("purpose_id[0]", str(purpose.id)),
                ("medication_id[0][]", str(medication.id)),
                ("dose[0][]", "1"),
                ("unit[0][]", "гр"),
                ("administration_method[0]", "внутривенно"),
                ("frequency[0]", "1 р/сут"),
                ("start_date[0]", "не дата"),
            ]
        )

        generated_text, errors = process_prescriptions(form)

        assert generated_text is None
        assert "Укажите корректную дату начала." in errors


# Проверка препарата, не связанного с выбранной целью терапии
def test_process_prescriptions_foreign_medication(app):
    with app.app_context():
        purpose = TherapyPurpose(
            name="Терапия",
            output_value="Терапия",
        )
        other_purpose = TherapyPurpose(
            name="Другая терапия",
            output_value="Другая терапия",
        )
        medication = TherapyMedication(
            name="Препарат",
            purposes=[other_purpose],
        )
        db.session.add_all([purpose, other_purpose, medication])
        db.session.commit()

        form = MultiDict(
            {
                "purpose_id[0]": str(purpose.id),
                "medication_id[0][]": [str(medication.id)],
                "dose[0][]": ["100"],
                "unit[0][]": ["мг"],
                "administration_method[0]": "внутривенно",
                "frequency[0]": "2 р/сут",
            }
        )
        generated_text, errors = process_prescriptions(form)

        assert generated_text is None
        assert "Выберите препараты, соответствующие цели терапии «Терапия»." in errors


# Проверка некорректной дозировки препарата
def test_process_category_form_drug_invalid_dose(app):
    with app.app_context():
        category = Category(
            name="Терапия",
            slug="therapy",
            order=1,
            template="",
        )
        db.session.add(category)
        db.session.commit()

        variable = TemplateVariable(
            category_id=category.id,
            name="drug",
            label="Препараты",
            field_type="multiselect",
            required=True,
        )
        db.session.add(variable)
        db.session.commit()

        option = VariableOption(
            variable_id=variable.id,
            value="Норадреналин",
            output_value="норадреналин",
        )
        db.session.add(option)
        db.session.commit()

        form = MultiDict(
            [
                ("drug", str(option.id)),
                (f"dose_{option.id}", "-0.5"),
            ]
        )

        values, errors = process_category_form(
            form,
            [variable],
            category,
        )

        assert values["drug"] == ""
        assert (
            "Дозировка препарата «Норадреналин» должна быть положительным числом."
            in errors
        )
