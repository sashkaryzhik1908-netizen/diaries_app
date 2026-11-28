import json

import pytest
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


# Создание пользователя
def create_user(app, username, is_admin=False, is_superuser=False):
    with app.app_context():
        user = User(
            username=username,
            password=generate_password_hash("123456"),
            is_admin=is_admin,
            is_superuser=is_superuser,
        )

        db.session.add(user)
        db.session.commit()

        return user.id


# Авторизация пользователя
def login(client, username):
    return client.post(
        "/login",
        data={
            "username": username,
            "password": "123456",
        },
        follow_redirects=True,
    )


# Создание тестовых назначений
def create_test_prescriptions(app, user_id):
    with app.app_context():
        diary = Diary(
            user_id=user_id,
            number=1,
        )

        category = Category(
            name="План интенсивной терапии",
            slug="prescriptions",
            order=1,
            template="",
        )

        purpose = TherapyPurpose(
            name="Используемая цель",
            output_value="используемая цель",
        )

        medication = TherapyMedication(
            name="Используемый препарат",
            purposes=[purpose],
        )

        db.session.add_all(
            [
                diary,
                category,
                purpose,
                medication,
            ]
        )
        db.session.flush()

        entry = DiaryEntry(
            diary_id=diary.id,
            category_id=category.id,
            text="Тестовые назначения",
            position=0,
            form_data=json.dumps(
                {
                    "purpose_id[0]": [str(purpose.id)],
                    "medication_id[0][]": [str(medication.id)],
                }
            ),
        )

        db.session.add(entry)
        db.session.commit()

        return {
            TherapyPurpose: purpose.id,
            TherapyMedication: medication.id,
        }


# Проверка доступа неавторизованного пользователя
@pytest.mark.parametrize("url", ["/admin/", "/admin/user/"])
def test_anonymous_cannot_access_admin(client, url):
    response = client.get(url)

    assert response.status_code == 403


# Проверка доступа обычного пользователя
@pytest.mark.parametrize("url", ["/admin/", "/admin/user/"])
def test_regular_user_cannot_access_admin(client, app, url):
    create_user(app, "regular_user")
    login(client, "regular_user")

    response = client.get(url)

    assert response.status_code == 403


# Проверка доступа администратора
@pytest.mark.parametrize("url", ["/admin/", "/admin/user/"])
def test_admin_cannot_access_superuser_panel(client, app, url):
    create_user(app, "admin", is_admin=True)
    login(client, "admin")

    response = client.get(url)

    assert response.status_code == 403


# Проверка доступа суперпользователя
@pytest.mark.parametrize("url", ["/admin/", "/admin/user/"])
def test_superuser_can_access_admin(client, app, url):
    create_user(
        app,
        "superuser",
        is_admin=True,
        is_superuser=True,
    )
    login(client, "superuser")

    response = client.get(url)

    assert response.status_code == 200


# Суперпользователь не может удалить собственную запись
def test_superuser_cannot_delete_self(client, app):
    user_id = create_user(
        app,
        "superuser",
        is_admin=True,
        is_superuser=True,
    )
    login(client, "superuser")

    response = client.post(
        "/admin/user/delete/",
        data={"id": user_id},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Нельзя удалить собственную учётную запись.".encode() in response.data

    with app.app_context():
        assert db.session.get(User, user_id) is not None


# Суперпользователь не может снять с себя права
def test_superuser_cannot_remove_own_permissions(client, app):
    user_id = create_user(
        app,
        "superuser",
        is_admin=True,
        is_superuser=True,
    )
    login(client, "superuser")

    response = client.post(
        f"/admin/user/edit/?id={user_id}",
        data={
            "is_admin": "y",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Нельзя снять с себя права суперпользователя.".encode() in response.data

    with app.app_context():
        user = db.session.get(User, user_id)

        assert user is not None
        assert user.is_superuser is True


# Массовое удаление пользователей запрещено
def test_bulk_user_deletion_is_disabled(client, app):
    superuser_id = create_user(
        app,
        "superuser",
        is_admin=True,
        is_superuser=True,
    )
    user_id = create_user(app, "regular_user")

    login(client, "superuser")

    client.post(
        "/admin/user/action/",
        data={
            "action": "delete",
            "rowid": [str(superuser_id), str(user_id)],
        },
        follow_redirects=True,
    )

    with app.app_context():
        assert db.session.get(User, superuser_id) is not None
        assert db.session.get(User, user_id) is not None


# Суперпользователь может удалить другого пользователя
def test_superuser_can_delete_other_user(client, app):
    create_user(
        app,
        "superuser",
        is_admin=True,
        is_superuser=True,
    )
    user_id = create_user(app, "regular_user")

    login(client, "superuser")

    response = client.post(
        "/admin/user/delete/",
        data={"id": user_id},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(User, user_id) is None


# Суперпользователь может назначить другого суперпользователя
def test_superuser_can_promote_other_user(client, app):
    create_user(
        app,
        "superuser",
        is_admin=True,
        is_superuser=True,
    )
    user_id = create_user(app, "regular_user")

    login(client, "superuser")

    response = client.post(
        f"/admin/user/edit/?id={user_id}",
        data={
            "is_admin": "y",
            "is_superuser": "y",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        user = db.session.get(User, user_id)

        assert user is not None
        assert user.is_admin is True
        assert user.is_superuser is True


# Запрет удаления используемых справочников терапии
@pytest.mark.parametrize(
    "model, endpoint, message",
    [
        (
            TherapyPurpose,
            "therapypurpose",
            "Нельзя удалить цель терапии, которая используется в дневнике.",
        ),
        (
            TherapyMedication,
            "therapymedication",
            "Нельзя удалить препарат, который используется в дневнике.",
        ),
    ],
)
def test_admin_cannot_delete_used_therapy_item(
    client,
    app,
    model,
    endpoint,
    message,
):
    user_id = create_user(
        app,
        "superuser",
        is_admin=True,
        is_superuser=True,
    )

    item_ids = create_test_prescriptions(app, user_id)
    item_id = item_ids[model]

    login(client, "superuser")

    response = client.post(
        f"/admin/{endpoint}/delete/",
        data={"id": item_id},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert message in response.get_data(as_text=True)

    with app.app_context():
        assert db.session.get(model, item_id) is not None


# Удаление неиспользуемых справочников терапии
@pytest.mark.parametrize(
    "model, endpoint",
    [
        (TherapyPurpose, "therapypurpose"),
        (TherapyMedication, "therapymedication"),
    ],
)
def test_admin_can_delete_unused_therapy_item(
    client,
    app,
    model,
    endpoint,
):
    create_user(
        app,
        "superuser",
        is_admin=True,
        is_superuser=True,
    )

    with app.app_context():
        if model is TherapyPurpose:
            item = TherapyPurpose(
                name="Неиспользуемая цель",
                output_value="неиспользуемая цель",
            )
        else:
            item = TherapyMedication(
                name="Неиспользуемый препарат",
            )

        db.session.add(item)
        db.session.commit()

        item_id = item.id

    login(client, "superuser")

    response = client.post(
        f"/admin/{endpoint}/delete/",
        data={"id": item_id},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(model, item_id) is None


# Запрет массового удаления справочников терапии
@pytest.mark.parametrize(
    "model, endpoint",
    [
        (TherapyPurpose, "therapypurpose"),
        (TherapyMedication, "therapymedication"),
    ],
)
def test_bulk_therapy_item_deletion_is_disabled(
    client,
    app,
    model,
    endpoint,
):
    user_id = create_user(
        app,
        "superuser",
        is_admin=True,
        is_superuser=True,
    )

    item_ids = create_test_prescriptions(app, user_id)
    used_item_id = item_ids[model]

    with app.app_context():
        if model is TherapyPurpose:
            unused_item = TherapyPurpose(
                name="Неиспользуемая цель",
                output_value="неиспользуемая цель",
            )
        else:
            unused_item = TherapyMedication(
                name="Неиспользуемый препарат",
            )

        db.session.add(unused_item)
        db.session.commit()

        unused_item_id = unused_item.id

    login(client, "superuser")

    response = client.post(
        f"/admin/{endpoint}/action/",
        data={
            "action": "delete",
            "rowid": [
                str(used_item_id),
                str(unused_item_id),
            ],
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(model, used_item_id) is not None
        assert db.session.get(model, unused_item_id) is not None
