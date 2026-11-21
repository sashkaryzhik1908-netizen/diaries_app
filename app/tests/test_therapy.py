import pytest

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import (
    User,
    Diary,
    TherapyPurpose,
    TherapyGroup,
    TherapyMedication,
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
        purpose = TherapyPurpose.query.filter_by(
            name="Коррекция гемодинамики",
        ).first()

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
        purposes = TherapyPurpose.query.filter_by(
            name="Коррекция гемодинамики",
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

        db.session.add_all([diary, purpose])
        db.session.commit()

        therapy_group = TherapyGroup(
            diary_id=diary.id,
            purpose_id=purpose.id,
            position=0,
        )
        db.session.add(therapy_group)
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
        medication = TherapyMedication.query.filter_by(
            name="Цефтриаксон",
        ).first()

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
        medications = TherapyMedication.query.filter_by(
            name="Цефтриаксон",
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
        assert TherapyMedication.query.count() == 0


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
