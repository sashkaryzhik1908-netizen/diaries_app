from sqlalchemy import func, select
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import (
    Category,
    Diary,
    DiaryEntry,
    TemplateVariable,
    User,
    VariableOption,
)


def create_user(username, is_admin=False):
    user = User(
        username=username,
        password=generate_password_hash("123456"),
        is_admin=is_admin,
    )
    db.session.add(user)
    db.session.commit()
    return user


def login(client, username):
    return client.post(
        "/login",
        data={"username": username, "password": "123456"},
    )


# Просмотр списка категорий
def test_list_categories(client, app):
    with app.app_context():
        create_user("user", is_admin=True)

        category_1 = Category(
            name="Неврологический статус",
            slug="neurological",
            order=2,
            template="Шаблон 1",
        )
        category_2 = Category(
            name="Жалобы",
            slug="complaints",
            order=1,
            template="Шаблон 2",
        )

        db.session.add_all([category_1, category_2])
        db.session.commit()

    login(client, "user")

    response = client.get("/categories")

    assert response.status_code == 200
    assert "Жалобы".encode() in response.data
    assert "Неврологический статус".encode() in response.data
    assert response.data.index("Жалобы".encode()) < response.data.index(
        "Неврологический статус".encode()
    )


# Просмотр отдельной категории
def test_view_category(client, app):
    with app.app_context():
        create_user("user", is_admin=True)

        category = Category(
            name="Жалобы",
            slug="complaints",
            order=1,
            template="Пациент предъявляет жалобы на...",
        )
        db.session.add(category)
        db.session.commit()

        variable = TemplateVariable(
            category_id=category.id,
            name="complaints",
            label="Жалобы пациента",
            field_type="text",
            required=True,
        )
        db.session.add(variable)
        db.session.commit()

        category_id = category.id

    login(client, "user")

    response = client.get(f"/categories/{category_id}")

    assert response.status_code == 200
    assert "Жалобы".encode() in response.data
    assert "Жалобы пациента".encode() in response.data


# Просмотр списка вариантов переменной
def test_list_options(client, app):
    with app.app_context():
        create_user("user", is_admin=True)

        category = Category(
            name="Состояние",
            slug="condition",
            order=1,
            template="Состояние пациента...",
        )
        db.session.add(category)
        db.session.commit()

        variable = TemplateVariable(
            category_id=category.id,
            name="condition",
            label="Общее состояние",
            field_type="select",
            required=True,
        )
        db.session.add(variable)
        db.session.commit()

        option_1 = VariableOption(
            variable_id=variable.id,
            value="Вариант 2",
            output_value="Вариант 2",
        )
        option_2 = VariableOption(
            variable_id=variable.id,
            value="Вариант 1",
            output_value="Вариант 1",
        )

        db.session.add_all([option_1, option_2])
        db.session.commit()

        variable_id = variable.id

    login(client, "user")

    response = client.get(f"/categories/{variable_id}/options")

    assert response.status_code == 200
    assert "Вариант 1".encode() in response.data
    assert "Вариант 2".encode() in response.data
    assert response.data.index("Вариант 1".encode()) < response.data.index(
        "Вариант 2".encode()
    )


# Добавление категории
def test_add_category(client, app):
    with app.app_context():
        admin = User(
            username="admin",
            name="Василий Пуповицкий",
            password=generate_password_hash("123456"),
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()

    login(client, "admin")

    response = client.post(
        "/categories/add",
        data={
            "name": "Жалобы",
            "slug": "complaints",
            "template": "Пациент предъявляет жалобы на...",
            "submit": "Сохранить изменения",
            "order": 1,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        category = db.session.scalar(
            select(Category).where(Category.slug == "complaints")
        )

        assert category is not None
        assert category.name == "Жалобы"
        assert category.order == 1


# Редактирование категории
def test_edit_category(client, app):
    with app.app_context():
        admin = User(
            username="admin",
            password=generate_password_hash("123456"),
            is_admin=True,
        )
        category = Category(
            name="Жалобы",
            slug="complaints",
            order=1,
            template="Старый шаблон",
        )

        db.session.add_all([admin, category])
        db.session.commit()

        category_id = category.id

    login(client, "admin")

    response = client.post(
        f"/categories/edit/{category_id}",
        data={
            "name": "Жалобы пациента",
            "slug": "patient_complaints",
            "template": "Новый шаблон",
            "submit": "Сохранить изменения",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        updated_category = db.session.get(Category, category_id)

        assert updated_category.name == "Жалобы пациента"
        assert updated_category.slug == "patient_complaints"
        assert updated_category.template == "Новый шаблон"


# Обычный пользователь не может добавлять категории
def test_user_cannot_add_category(client, app):
    with app.app_context():
        create_user("user")

    login(client, "user")

    response = client.post(
        "/categories/add",
        data={
            "name": "Жалобы",
            "slug": "complaints",
            "template": "Шаблон",
        },
    )

    assert response.status_code == 403

    with app.app_context():
        assert db.session.scalar(select(func.count()).select_from(Category)) == 0


# Удаление категории
def test_delete_category(client, app):
    with app.app_context():
        admin = User(
            username="admin",
            password=generate_password_hash("123456"),
            is_admin=True,
        )
        category = Category(
            name="Жалобы",
            slug="complaints",
            order=1,
            template="Шаблон",
        )

        db.session.add_all([admin, category])
        db.session.commit()

        category_id = category.id

    login(client, "admin")

    response = client.post(
        f"/categories/delete/{category_id}",
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(Category, category_id) is None


# Нельзя удалить категорию, которая используется в дневниках
def test_cannot_delete_category_with_entries(client, app):
    with app.app_context():
        admin = User(
            username="admin",
            password=generate_password_hash("123456"),
            is_admin=True,
        )
        diary_user = User(
            username="diary_user",
            password=generate_password_hash("123456"),
            is_admin=False,
        )
        db.session.add_all([admin, diary_user])
        db.session.commit()

        category = Category(
            name="Жалобы",
            slug="complaints",
            order=1,
            template="Шаблон",
        )
        diary = Diary(
            user_id=diary_user.id,
            number=1,
        )

        db.session.add_all([category, diary])
        db.session.commit()

        entry = DiaryEntry(
            diary_id=diary.id,
            category_id=category.id,
            text="Жалобы на головную боль",
            position=1,
        )

        db.session.add(entry)
        db.session.commit()

        category_id = category.id

    login(client, "admin")

    response = client.post(
        f"/categories/delete/{category_id}",
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(Category, category_id) is not None
        assert (
            db.session.scalar(
                select(DiaryEntry).where(DiaryEntry.category_id == category_id).limit(1)
            )
            is not None
        )


# Добавление переменной
def test_add_variable(client, app):
    with app.app_context():
        admin = User(
            username="admin",
            password=generate_password_hash("123456"),
            is_admin=True,
        )
        category = Category(
            name="Жалобы",
            slug="complaints",
            order=1,
            template="Пациент предъявляет жалобы на...",
        )
        db.session.add_all([admin, category])
        db.session.commit()
        category_id = category.id

    login(client, "admin")

    response = client.post(
        f"/categories/{category_id}/add_variable",
        data={
            "name": "complaints",
            "label": "Жалобы пациента",
            "field_type": "text",
            "required": "y",
            "order": 1,
            "submit": "Сохранить",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        variable = db.session.scalar(
            select(TemplateVariable).where(
                TemplateVariable.category_id == category_id,
                TemplateVariable.name == "complaints",
            )
        )
        assert variable is not None
        assert variable.label == "Жалобы пациента"


# Редактирование переменной
def test_edit_variable(client, app):
    with app.app_context():
        admin = User(
            username="admin",
            password=generate_password_hash("123456"),
            is_admin=True,
        )
        category = Category(
            name="Жалобы",
            slug="complaints",
            order=1,
            template="Шаблон",
        )
        db.session.add_all([admin, category])
        db.session.commit()

        variable = TemplateVariable(
            category_id=category.id,
            name="complaints",
            label="Старое название",
            field_type="text",
            required=False,
        )
        db.session.add(variable)
        db.session.commit()
        variable_id = variable.id

    login(client, "admin")

    response = client.post(
        f"/categories/edit_variable/{variable_id}",
        data={
            "name": "patient_complaints",
            "label": "Новые жалобы",
            "field_type": "text",
            "required": "y",
            "submit": "Сохранить",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        variable = db.session.get(TemplateVariable, variable_id)
        assert variable.name == "patient_complaints"
        assert variable.label == "Новые жалобы"
        assert variable.required is True


# Обычный пользователь не может добавлять переменные
def test_user_cannot_add_variable(client, app):
    with app.app_context():
        create_user("user")

        category = Category(
            name="Жалобы",
            slug="complaints",
            order=1,
            template="Шаблон",
        )
        db.session.add(category)
        db.session.commit()
        category_id = category.id

    login(client, "user")

    response = client.post(
        f"/categories/{category_id}/add_variable",
        data={
            "name": "complaints",
            "label": "Жалобы",
            "field_type": "text",
        },
    )

    assert response.status_code == 403


# Удаление переменной вместе с её вариантами
def test_delete_variable_cascades_options(client, app):
    with app.app_context():
        admin = User(
            username="admin",
            password=generate_password_hash("123456"),
            is_admin=True,
        )
        category = Category(
            name="Состояние",
            slug="condition",
            order=1,
            template="Шаблон",
        )
        db.session.add_all([admin, category])
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

        option = VariableOption(
            variable_id=variable.id,
            value="Тяжёлое",
            output_value="тяжёлое",
        )
        db.session.add(option)
        db.session.commit()

        variable_id = variable.id
        option_id = option.id

    login(client, "admin")

    response = client.post(
        f"/categories/del_variable/{variable_id}",
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(TemplateVariable, variable_id) is None
        assert db.session.get(VariableOption, option_id) is None


# Обычный пользователь не может редактировать переменную
def test_user_cannot_edit_variable(client, app):
    with app.app_context():
        create_user("user")
        category = Category(
            name="Жалобы",
            slug="complaints",
            order=1,
            template="Шаблон",
        )
        db.session.add(category)
        db.session.commit()

        variable = TemplateVariable(
            category_id=category.id,
            name="complaints",
            label="Жалобы",
            field_type="text",
            required=False,
        )
        db.session.add(variable)
        db.session.commit()
        variable_id = variable.id

    login(client, "user")

    response = client.post(
        f"/categories/edit_variable/{variable_id}",
        data={
            "name": "changed",
            "label": "Изменено",
            "field_type": "text",
        },
    )

    assert response.status_code == 403


# Добавление варианта
def test_add_option(client, app):
    with app.app_context():
        admin = User(
            username="admin",
            password=generate_password_hash("123456"),
            is_admin=True,
        )
        category = Category(
            name="Состояние",
            slug="condition",
            order=1,
            template="Шаблон",
        )
        db.session.add_all([admin, category])
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
        variable_id = variable.id

    login(client, "admin")

    response = client.post(
        f"/variables/{variable_id}/add_option",
        data={
            "value": "Тяжёлое",
            "output_value": "тяжёлое",
            "submit": "Сохранить",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        option = db.session.scalar(
            select(VariableOption)
            .where(
                VariableOption.variable_id == variable_id,
                VariableOption.value == "Тяжёлое",
            )
            .limit(1)
        )
        assert option is not None
        assert option.output_value == "тяжёлое"


# Редактирование варианта
def test_edit_option(client, app):
    with app.app_context():
        admin = User(
            username="admin",
            password=generate_password_hash("123456"),
            is_admin=True,
        )
        category = Category(
            name="Состояние",
            slug="condition",
            order=1,
            template="Шаблон",
        )
        db.session.add_all([admin, category])
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

        option = VariableOption(
            variable_id=variable.id,
            value="Старое",
            output_value="старое",
        )
        db.session.add(option)
        db.session.commit()

        variable_id = variable.id
        option_id = option.id

    login(client, "admin")

    response = client.post(
        f"/variables/{variable_id}/options/{option_id}/edit",
        data={
            "value": "Новое",
            "output_value": "новое",
            "submit": "Сохранить",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        option = db.session.get(VariableOption, option_id)
        assert option.value == "Новое"
        assert option.output_value == "новое"


# Обычный пользователь не может добавлять варианты
def test_user_cannot_add_option(client, app):
    with app.app_context():
        create_user("user")
        category = Category(
            name="Состояние",
            slug="condition",
            order=1,
            template="Шаблон",
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
        variable_id = variable.id

    login(client, "user")

    response = client.post(
        f"/variables/{variable_id}/add_option",
        data={
            "value": "Тяжёлое",
            "output_value": "тяжёлое",
        },
    )

    assert response.status_code == 403


# Нельзя редактировать вариант, принадлежащий другой переменной
def test_edit_option_wrong_variable_returns_404(client, app):
    with app.app_context():
        admin = User(
            username="admin",
            password=generate_password_hash("123456"),
            is_admin=True,
        )
        category = Category(
            name="Состояние",
            slug="condition",
            order=1,
            template="Шаблон",
        )
        db.session.add_all([admin, category])
        db.session.commit()

        variable_1 = TemplateVariable(
            category_id=category.id,
            name="condition",
            label="Состояние",
            field_type="select",
            required=True,
        )
        variable_2 = TemplateVariable(
            category_id=category.id,
            name="condition_extra",
            label="Дополнительное состояние",
            field_type="select",
            required=False,
        )
        db.session.add_all([variable_1, variable_2])
        db.session.commit()

        option = VariableOption(
            variable_id=variable_1.id,
            value="Тяжёлое",
            output_value="тяжёлое",
        )
        db.session.add(option)
        db.session.commit()

        variable_id = variable_2.id
        option_id = option.id

    login(client, "admin")

    response = client.post(
        f"/variables/{variable_id}/options/{option_id}/edit",
        data={
            "value": "Изменено",
            "output_value": "изменено",
        },
    )

    assert response.status_code == 404


# Нельзя удалить вариант, принадлежащий другой переменной
def test_delete_option_wrong_variable_returns_404(client, app):
    with app.app_context():
        admin = User(
            username="admin",
            password=generate_password_hash("123456"),
            is_admin=True,
        )
        category = Category(
            name="Состояние",
            slug="condition",
            order=1,
            template="Шаблон",
        )
        db.session.add_all([admin, category])
        db.session.commit()

        variable_1 = TemplateVariable(
            category_id=category.id,
            name="condition",
            label="Состояние",
            field_type="select",
            required=True,
        )
        variable_2 = TemplateVariable(
            category_id=category.id,
            name="condition_extra",
            label="Дополнительное состояние",
            field_type="select",
            required=False,
        )
        db.session.add_all([variable_1, variable_2])
        db.session.commit()

        option = VariableOption(
            variable_id=variable_1.id,
            value="Тяжёлое",
            output_value="тяжёлое",
        )
        db.session.add(option)
        db.session.commit()

        variable_id = variable_2.id
        option_id = option.id

    login(client, "admin")

    response = client.post(
        f"/variables/{variable_id}/options/{option_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 404
