from flask import url_for
from sqlalchemy import func, select
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Category, Diary, DiaryEntry, User


# Создание тестового пользователя
def create_user(username):
    user = User(
        username=username,
        password=generate_password_hash("123456"),
        is_admin=False,
    )

    db.session.add(user)
    db.session.commit()

    return user


# Вход пользователя
def login(client, username):
    return client.post(
        "/login",
        data={
            "username": username,
            "password": "123456",
        },
    )


# Проверка создания дневника
def test_create_diary(client, app):
    with app.app_context():
        create_user("user1")

    login(client, "user1")

    response = client.post(
        "/diaries/create",
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        diary = db.session.scalar(select(Diary).limit(1))

        assert diary is not None
        assert diary.number == 1

        user = db.session.get(User, diary.user_id)
        assert user.username == "user1"


# Проверка индивидуальной нумерации дневников
def test_diary_numbering_per_user(client, app):
    with app.app_context():
        user1 = create_user("user1")
        user2 = create_user("user2")

        user1_id = user1.id
        user2_id = user2.id

    # Первый пользователь создаёт два дневника
    login(client, "user1")

    client.post("/diaries/create")
    client.post("/diaries/create")

    # Второй пользователь создаёт один дневник
    client.post("/logout")
    login(client, "user2")

    client.post("/diaries/create")

    with app.app_context():
        user1_diaries = db.session.scalars(
            select(Diary).where(Diary.user_id == user1_id).order_by(Diary.number)
        ).all()

        user2_diaries = db.session.scalars(
            select(Diary).where(Diary.user_id == user2_id).order_by(Diary.number)
        ).all()

        assert [diary.number for diary in user1_diaries] == [1, 2]
        assert [diary.number for diary in user2_diaries] == [1]


# Проверка отображения только собственных дневников
def test_user_sees_only_own_diaries(client, app):
    with app.app_context():
        user1 = create_user("user1")
        user2 = create_user("user2")

        diary1 = Diary(user_id=user1.id, number=1)
        diary2 = Diary(user_id=user2.id, number=1)

        db.session.add_all([diary1, diary2])
        db.session.commit()

        diary1_id = diary1.id
        diary2_id = diary2.id

    login(client, "user1")

    response = client.get("/diaries")

    assert response.status_code == 200

    with app.test_request_context():
        diary1_url = url_for(
            "diaries.view_diary",
            diary_id=diary1_id,
        )

        diary2_url = url_for(
            "diaries.view_diary",
            diary_id=diary2_id,
        )

    assert diary1_url.encode() in response.data
    assert diary2_url.encode() not in response.data


# Проверка запрета доступа к чужому дневнику
def test_user_cannot_open_another_users_diary(client, app):
    with app.app_context():
        create_user("user1")
        user2 = create_user("user2")

        diary = Diary(user_id=user2.id, number=1)

        db.session.add(diary)
        db.session.commit()

        diary_id = diary.id

    login(client, "user1")

    response = client.get(f"/diaries/{diary_id}")

    assert response.status_code == 404


# Проверка обработки ошибки при создании дневника
def test_create_diary_commit_error(client, app, monkeypatch):
    with app.app_context():
        create_user("user1")

    login(client, "user1")

    def fail_commit():
        raise RuntimeError("Ошибка тестового сохранения")

    monkeypatch.setattr(db.session, "commit", fail_commit)

    response = client.post("/diaries/create")

    assert response.status_code == 302
    assert response.location.endswith("/diaries")

    with app.app_context():
        assert db.session.scalar(select(func.count()).select_from(Diary)) == 0


# Проверка успешного удаления дневника
def test_delete_diary(client, app):
    with app.app_context():
        user = create_user("user1")

        diary = Diary(
            user_id=user.id,
            number=1,
        )

        db.session.add(diary)
        db.session.commit()

        diary_id = diary.id

    login(client, "user1")

    response = client.post(f"/diaries/{diary_id}/delete")

    assert response.status_code == 302
    assert response.location.endswith("/diaries")

    with app.app_context():
        assert db.session.get(Diary, diary_id) is None


# Проверка обработки ошибки при удалении дневника
def test_delete_diary_commit_error(client, app, monkeypatch):
    with app.app_context():
        user = create_user("user1")

        diary = Diary(
            user_id=user.id,
            number=1,
        )

        db.session.add(diary)
        db.session.commit()

        diary_id = diary.id

    login(client, "user1")

    def fail_commit():
        raise RuntimeError("Ошибка тестового сохранения")

    monkeypatch.setattr(db.session, "commit", fail_commit)

    response = client.post(f"/diaries/{diary_id}/delete")

    assert response.status_code == 302
    assert response.location.endswith("/diaries")

    with app.app_context():
        assert db.session.get(Diary, diary_id) is not None


# Проверка отображения синдромов в дневнике
def test_view_diary_with_syndromes(client, app):
    with app.app_context():
        user = create_user("user1")

        diary = Diary(
            user_id=user.id,
            number=1,
        )

        condition = Category(
            name="Состояние",
            slug="condition",
            order=1,
            template="Состояние тяжёлое",
        )

        prescriptions = Category(
            name="Назначения",
            slug="prescriptions",
            order=2,
            template="",
        )

        db.session.add_all([diary, condition, prescriptions])
        db.session.commit()

        condition_entry = DiaryEntry(
            diary_id=diary.id,
            category_id=condition.id,
            text="Состояние тяжёлое",
            position=0,
            syndromes="Интоксикация, ВЭН",
        )

        prescriptions_entry = DiaryEntry(
            diary_id=diary.id,
            category_id=prescriptions.id,
            text="Назначения",
            position=1,
            syndromes="",
        )

        db.session.add_all([condition_entry, prescriptions_entry])
        db.session.commit()

        diary_id = diary.id

    login(client, "user1")

    response = client.get(f"/diaries/{diary_id}")

    assert response.status_code == 200
    assert "Интоксикация".encode() in response.data
    assert "ВЭН".encode() in response.data


# Проверка отображения дневника без синдромов
def test_view_diary_without_syndromes(client, app):
    with app.app_context():
        user = create_user("user1")

        diary = Diary(
            user_id=user.id,
            number=1,
        )

        db.session.add(diary)
        db.session.commit()

        diary_id = diary.id

    login(client, "user1")

    response = client.get(f"/diaries/{diary_id}")

    assert response.status_code == 200
