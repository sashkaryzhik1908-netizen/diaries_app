import json

import pytest
from sqlalchemy import func, select
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import (
    Category,
    Diary,
    DiaryEntry,
    TherapyMedication,
    TherapyPurpose,
    User,
)
from app.services.therapy_service import (
    is_medication_used,
    is_purpose_used,
    validate_purpose_ids,
)


# Создание пользователя
def create_user(username, is_admin=False):
    user = User(
        username=username,
        password=generate_password_hash("123456"),
        is_admin=is_admin,
    )
    db.session.add(user)
    db.session.commit()
    return user


# Создание администратора
def create_admin(username):
    return create_user(username, is_admin=True)


# Авторизация пользователя
def login(client, username):
    return client.post(
        "/login",
        data={
            "username": username,
            "password": "123456",
        },
    )


# Создание записи назначений для тестирования
def create_prescription_entry(user, form_data):
    diary = Diary(
        user_id=user.id,
        number=1,
    )

    category = Category(
        name="План интенсивной терапии",
        slug="prescriptions",
        order=1,
        template="",
    )

    db.session.add_all([diary, category])
    db.session.flush()

    entry = DiaryEntry(
        diary_id=diary.id,
        category_id=category.id,
        text="Тестовые назначения",
        position=0,
        form_data=form_data,
    )

    db.session.add(entry)
    db.session.commit()

    return entry


# Проверка страницы целей терапии
def test_list_therapy_purposes(client, app):
    with app.app_context():
        create_admin("admin")

        db.session.add_all(
            [
                TherapyPurpose(
                    name="Цель 2",
                    output_value="Цель 2",
                ),
                TherapyPurpose(
                    name="Цель 1",
                    output_value="Цель 1",
                ),
            ]
        )
        db.session.commit()

    login(client, "admin")

    response = client.get("/therapy/purposes")

    assert response.status_code == 200
    assert "Цель 1" in response.get_data(as_text=True)
    assert "Цель 2" in response.get_data(as_text=True)


# Проверка сортировки целей терапии
def test_therapy_purposes_order(client, app):
    with app.app_context():
        create_admin("admin")

        db.session.add_all(
            [
                TherapyPurpose(
                    name="Цель 3",
                    output_value="Цель 3",
                ),
                TherapyPurpose(
                    name="Цель 1",
                    output_value="Цель 1",
                ),
                TherapyPurpose(
                    name="Цель 2",
                    output_value="Цель 2",
                ),
            ]
        )
        db.session.commit()

    login(client, "admin")

    response = client.get("/therapy/purposes")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert html.index("Цель 1") < html.index("Цель 2")
    assert html.index("Цель 2") < html.index("Цель 3")


# Проверка страницы препаратов
def test_list_therapy_medications(client, app):
    with app.app_context():
        create_admin("admin")

        db.session.add_all(
            [
                TherapyMedication(name="Цефтриаксон"),
                TherapyMedication(name="Амикацин"),
            ]
        )
        db.session.commit()

    login(client, "admin")

    response = client.get("/therapy/medications")

    assert response.status_code == 200
    assert "Цефтриаксон" in response.get_data(as_text=True)
    assert "Амикацин" in response.get_data(as_text=True)


# Проверка сортировки препаратов по названию
def test_therapy_medications_order(client, app):
    with app.app_context():
        create_admin("admin")

        db.session.add_all(
            [
                TherapyMedication(name="Цефтриаксон"),
                TherapyMedication(name="Амикацин"),
                TherapyMedication(name="Ванкомицин"),
            ]
        )
        db.session.commit()

    login(client, "admin")

    response = client.get("/therapy/medications")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert html.index("Амикацин") < html.index("Ванкомицин")
    assert html.index("Ванкомицин") < html.index("Цефтриаксон")


# Добавление цели терапии
def test_add_therapy_purpose(client, app):
    with app.app_context():
        create_admin("admin")

    login(client, "admin")

    response = client.post(
        "/therapy/purposes/add",
        data={
            "name": "Коррекция гемодинамики",
            "output_value": "коррекция гемодинамики",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Цель терапии добавлена." in response.get_data(as_text=True)

    with app.app_context():
        purpose = db.session.scalar(
            select(TherapyPurpose).where(
                TherapyPurpose.name == "Коррекция гемодинамики",
            )
        )

        assert purpose is not None
        assert purpose.output_value == "коррекция гемодинамики"


# Запрет добавления дублирующей цели терапии
def test_add_duplicate_therapy_purpose(client, app):
    with app.app_context():
        create_admin("admin")

        db.session.add(
            TherapyPurpose(
                name="Коррекция гемодинамики",
                output_value="коррекция гемодинамики",
            )
        )
        db.session.commit()

    login(client, "admin")

    response = client.post(
        "/therapy/purposes/add",
        data={
            "name": "Коррекция гемодинамики",
            "output_value": "другое значение",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Такая цель терапии уже существует." in response.get_data(as_text=True)

    with app.app_context():
        purposes = db.session.scalars(
            select(TherapyPurpose).where(
                TherapyPurpose.name == "Коррекция гемодинамики",
            )
        ).all()
        assert len(purposes) == 1


# Редактирование цели терапии
def test_edit_therapy_purpose(client, app):
    with app.app_context():
        create_admin("admin")

        purpose = TherapyPurpose(
            name="Старая цель",
            output_value="старое значение",
        )
        db.session.add(purpose)
        db.session.commit()

        purpose_id = purpose.id

    login(client, "admin")

    response = client.post(
        f"/therapy/purposes/{purpose_id}/edit",
        data={
            "name": "Новая цель",
            "output_value": "новое значение",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Цель терапии успешно изменена." in response.get_data(as_text=True)

    with app.app_context():
        purpose = db.session.get(TherapyPurpose, purpose_id)

        assert purpose.name == "Новая цель"
        assert purpose.output_value == "новое значение"


# Запрет изменения цели на существующее название
def test_edit_therapy_purpose_duplicate(client, app):
    with app.app_context():
        create_admin("admin")

        purposes = [
            TherapyPurpose(
                name="Первая цель",
                output_value="первая",
            ),
            TherapyPurpose(
                name="Вторая цель",
                output_value="вторая",
            ),
        ]

        db.session.add_all(purposes)
        db.session.commit()

        purpose_id = purposes[0].id

    login(client, "admin")

    response = client.post(
        f"/therapy/purposes/{purpose_id}/edit",
        data={
            "name": "Вторая цель",
            "output_value": "изменённое значение",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Такая цель терапии уже существует." in response.get_data(as_text=True)

    with app.app_context():
        purpose = db.session.get(TherapyPurpose, purpose_id)

        assert purpose.name == "Первая цель"
        assert purpose.output_value == "первая"


# Несуществующая цель терапии
def test_edit_nonexistent_therapy_purpose(client, app):
    with app.app_context():
        create_admin("admin")

    login(client, "admin")

    response = client.get("/therapy/purposes/999/edit")

    assert response.status_code == 404


# Удаление цели терапии
def test_delete_therapy_purpose(client, app):
    with app.app_context():
        create_admin("admin")

        purpose = TherapyPurpose(
            name="Тестовая цель",
            output_value="тест",
        )
        db.session.add(purpose)
        db.session.commit()

        purpose_id = purpose.id

    login(client, "admin")

    response = client.post(
        f"/therapy/purposes/{purpose_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Цель терапии удалена." in response.get_data(as_text=True)

    with app.app_context():
        assert db.session.get(TherapyPurpose, purpose_id) is None


# Запрет удаления используемой цели терапии
def test_delete_used_therapy_purpose(client, app):
    with app.app_context():
        user = create_admin("admin")

        diary = Diary(
            user_id=user.id,
            number=1,
        )

        purpose = TherapyPurpose(
            name="Используемая цель",
            output_value="тест",
        )

        category = Category(
            name="План интенсивной терапии",
            slug="prescriptions",
            order=1,
            template="",
        )

        db.session.add_all([diary, purpose, category])
        db.session.commit()

        entry = DiaryEntry(
            diary_id=diary.id,
            category_id=category.id,
            text="Тестовые назначения",
            position=0,
            form_data=json.dumps(
                {
                    "purpose_id[0]": [str(purpose.id)],
                }
            ),
        )

        db.session.add(entry)
        db.session.commit()

        purpose_id = purpose.id

    login(client, "admin")

    response = client.post(
        f"/therapy/purposes/{purpose_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert (
        "Нельзя удалить цель терапии, которая используется в дневнике."
        in response.get_data(as_text=True)
    )

    with app.app_context():
        assert db.session.get(TherapyPurpose, purpose_id) is not None


# Проверка неиспользуемой цели терапии при наличии назначений
def test_is_purpose_used_other_purpose(app):
    with app.app_context():
        user = create_admin("admin")

        diary = Diary(
            user_id=user.id,
            number=1,
        )

        category = Category(
            name="План интенсивной терапии",
            slug="prescriptions",
            order=1,
            template="",
        )

        used_purpose = TherapyPurpose(
            name="Используемая цель",
            output_value="используемая",
        )

        unused_purpose = TherapyPurpose(
            name="Неиспользуемая цель",
            output_value="неиспользуемая",
        )

        db.session.add_all([diary, category, used_purpose, unused_purpose])
        db.session.commit()

        entry = DiaryEntry(
            diary_id=diary.id,
            category_id=category.id,
            text="Тестовые назначения",
            position=0,
            form_data=json.dumps(
                {
                    "purpose_id[0]": [str(used_purpose.id)],
                }
            ),
        )

        db.session.add(entry)
        db.session.commit()

        assert is_purpose_used(used_purpose.id) is True
        assert is_purpose_used(unused_purpose.id) is False


# Проверка повреждённых данных назначений
def test_is_purpose_used_invalid_json(app):
    with app.app_context():
        user = create_admin("admin")

        diary = Diary(
            user_id=user.id,
            number=1,
        )

        category = Category(
            name="План интенсивной терапии",
            slug="prescriptions",
            order=1,
            template="",
        )

        purpose = TherapyPurpose(
            name="Тестовая цель",
            output_value="тест",
        )

        db.session.add_all([diary, category, purpose])
        db.session.commit()

        entry = DiaryEntry(
            diary_id=diary.id,
            category_id=category.id,
            text="Тестовые назначения",
            position=0,
            form_data="invalid json",
        )

        db.session.add(entry)
        db.session.commit()

        assert is_purpose_used(purpose.id) is True


# Добавление препарата
def test_add_therapy_medication(client, app):
    with app.app_context():
        create_admin("admin")

    login(client, "admin")

    response = client.post(
        "/therapy/medications/add",
        data={"name": "Цефтриаксон"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Препарат успешно добавлен." in response.get_data(as_text=True)

    with app.app_context():
        medication = db.session.scalar(
            select(TherapyMedication)
            .where(TherapyMedication.name == "Цефтриаксон")
            .limit(1)
        )

        assert medication is not None


# Запрет добавления дублирующего препарата
def test_add_duplicate_therapy_medication(client, app):
    with app.app_context():
        create_admin("admin")

        db.session.add(TherapyMedication(name="Цефтриаксон"))
        db.session.commit()

    login(client, "admin")

    response = client.post(
        "/therapy/medications/add",
        data={"name": "Цефтриаксон"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Такой препарат уже есть в справочнике." in response.get_data(as_text=True)

    with app.app_context():
        medications = db.session.scalars(
            select(TherapyMedication).where(
                TherapyMedication.name == "Цефтриаксон",
            )
        ).all()

        assert len(medications) == 1


# Проверка обязательного названия препарата
def test_add_therapy_medication_without_name(client, app):
    with app.app_context():
        create_admin("admin")

    login(client, "admin")

    response = client.post(
        "/therapy/medications/add",
        data={"name": ""},
    )

    assert response.status_code == 200

    with app.app_context():
        assert (
            db.session.scalar(select(func.count()).select_from(TherapyMedication)) == 0
        )


# Редактирование препарата
def test_edit_therapy_medication(client, app):
    with app.app_context():
        create_admin("admin")

        medication = TherapyMedication(name="Старое название")
        db.session.add(medication)
        db.session.commit()

        medication_id = medication.id

    login(client, "admin")

    response = client.post(
        f"/therapy/medications/{medication_id}/edit",
        data={"name": "Новое название"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Название препарата изменено." in response.get_data(as_text=True)

    with app.app_context():
        medication = db.session.get(TherapyMedication, medication_id)
        assert medication.name == "Новое название"


# Запрет изменения названия на существующее
def test_edit_therapy_medication_duplicate(client, app):
    with app.app_context():
        create_admin("admin")

        medications = [
            TherapyMedication(name="Первый препарат"),
            TherapyMedication(name="Второй препарат"),
        ]
        db.session.add_all(medications)
        db.session.commit()

        medication_id = medications[0].id

    login(client, "admin")

    response = client.post(
        f"/therapy/medications/{medication_id}/edit",
        data={"name": "Второй препарат"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Такой препарат уже есть в справочнике." in response.get_data(as_text=True)

    with app.app_context():
        medication = db.session.get(TherapyMedication, medication_id)
        assert medication.name == "Первый препарат"


# Удаление препарата
def test_delete_therapy_medication(client, app):
    with app.app_context():
        create_admin("admin")

        medication = TherapyMedication(name="Тестовый препарат")
        db.session.add(medication)
        db.session.commit()

        medication_id = medication.id

    login(client, "admin")

    response = client.post(
        f"/therapy/medications/{medication_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Препарат удалён из справочника." in response.get_data(as_text=True)

    with app.app_context():
        assert db.session.get(TherapyMedication, medication_id) is None


# Запрет удаления используемого препарата
def test_delete_used_therapy_medication(client, app):
    with app.app_context():
        user = create_admin("admin")

        purpose = TherapyPurpose(
            name="Тестовая цель",
            output_value="тестовая цель",
        )

        medication = TherapyMedication(
            name="Используемый препарат",
            purposes=[purpose],
        )

        db.session.add_all([purpose, medication])
        db.session.flush()

        create_prescription_entry(
            user,
            json.dumps(
                {
                    "purpose_id[0]": [str(purpose.id)],
                    "medication_id[0][]": [str(medication.id)],
                }
            ),
        )

        medication_id = medication.id

    login(client, "admin")

    response = client.post(
        f"/therapy/medications/{medication_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert (
        "Нельзя удалить препарат, который используется в дневнике."
        in response.get_data(as_text=True)
    )

    with app.app_context():
        assert db.session.get(TherapyMedication, medication_id) is not None


# Несуществующий препарат
def test_edit_nonexistent_therapy_medication(client, app):
    with app.app_context():
        create_admin("admin")

    login(client, "admin")

    response = client.get("/therapy/medications/999/edit")

    assert response.status_code == 404


# Проверка запрета доступа обычному пользователю
@pytest.mark.parametrize(
    "url, method",
    [
        ("/therapy/purposes/add", "get"),
        ("/therapy/purposes/999/edit", "get"),
        ("/therapy/purposes/999/delete", "post"),
        ("/therapy/medications/add", "get"),
        ("/therapy/medications/999/edit", "get"),
        ("/therapy/medications/999/delete", "post"),
    ],
)
def test_therapy_routes_forbidden_for_regular_user(
    client,
    app,
    url,
    method,
):
    with app.app_context():
        create_user("user1")

    login(client, "user1")

    response = getattr(client, method)(url)

    assert response.status_code == 403


# Проверка корректных идентификаторов целей терапии
def test_validate_purpose_ids_valid(app):
    with app.app_context():
        purpose = TherapyPurpose(
            name="Тестовая терапия",
            output_value="Тестовая терапия",
        )

        db.session.add(purpose)
        db.session.commit()

        purpose_ids, error = validate_purpose_ids(str(purpose.id))

        assert purpose_ids == [purpose.id]
        assert error is None


# Проверка некорректного идентификатора
def test_validate_purpose_ids_invalid(app):
    with app.app_context():
        purpose_ids, error = validate_purpose_ids("abc")

        assert purpose_ids == []
        assert error == "Некорректные идентификаторы целей терапии."


# Проверка повторяющихся идентификаторов
def test_validate_purpose_ids_duplicate(app):
    with app.app_context():
        purpose_ids, error = validate_purpose_ids("1,1")

        assert purpose_ids == []
        assert error == "Цели терапии не должны повторяться."


# Проверка несуществующего идентификатора
def test_validate_purpose_ids_nonexistent(app):
    with app.app_context():
        purpose_ids, error = validate_purpose_ids("999999")

        assert purpose_ids == []
        assert error == "Выбраны несуществующие цели терапии."


# Проверка пустого списка целей терапии
def test_validate_purpose_ids_empty(app):
    with app.app_context():
        purpose_ids, error = validate_purpose_ids("")

        assert purpose_ids == []
        assert error is None


# Проверка использования препарата в назначениях
@pytest.mark.parametrize("group_index", [0, 1])
def test_is_medication_used(app, group_index):
    with app.app_context():
        user = create_admin("admin")

        used_medication = TherapyMedication(
            name="Используемый препарат",
        )

        unused_medication = TherapyMedication(
            name="Неиспользуемый препарат",
        )

        db.session.add_all(
            [
                used_medication,
                unused_medication,
            ]
        )
        db.session.flush()

        create_prescription_entry(
            user,
            json.dumps(
                {
                    f"medication_id[{group_index}][]": [
                        str(used_medication.id),
                    ],
                }
            ),
        )

        assert is_medication_used(used_medication.id) is True
        assert is_medication_used(unused_medication.id) is False


# Проверка повреждённых данных назначений
@pytest.mark.parametrize(
    "form_data",
    [
        "invalid json",
        "[]",
        "null",
        '{"medication_id[0][]": "1"}',
    ],
)
def test_is_medication_used_invalid_data(app, form_data):
    with app.app_context():
        user = create_admin("admin")

        medication = TherapyMedication(
            name="Тестовый препарат",
        )

        db.session.add(medication)
        db.session.flush()

        create_prescription_entry(user, form_data)

        assert is_medication_used(medication.id) is True


# Проверка независимости идентификаторов целей и препаратов
def test_is_medication_used_matching_purpose_id(app):
    with app.app_context():
        user = create_admin("admin")

        purpose = TherapyPurpose(
            id=100,
            name="Тестовая цель",
            output_value="тестовая цель",
        )

        medication = TherapyMedication(
            id=100,
            name="Тестовый препарат",
        )

        db.session.add_all([purpose, medication])
        db.session.flush()

        create_prescription_entry(
            user,
            json.dumps(
                {
                    "purpose_id[0]": [str(purpose.id)],
                }
            ),
        )

        assert purpose.id == medication.id
        assert is_purpose_used(purpose.id) is True
        assert is_medication_used(medication.id) is False
