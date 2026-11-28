from flask import abort, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from sqlalchemy import func, select

from app.extensions import db
from app.services.therapy_service import (
    is_medication_used,
    is_purpose_used,
)

from .models import (
    Category,
    Diary,
    TemplateVariable,
    TherapyMedication,
    TherapyPurpose,
    TherapySource,
    TherapySourceValue,
    User,
    VariableOption,
)


class SuperuserAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    @expose("/")
    def index(self):
        stats = {
            "users": db.session.scalar(select(func.count()).select_from(User)),
            "categories": db.session.scalar(select(func.count()).select_from(Category)),
            "variables": db.session.scalar(
                select(func.count()).select_from(TemplateVariable)
            ),
            "options": db.session.scalar(
                select(func.count()).select_from(VariableOption)
            ),
        }

        return self.render("admin/index.html", stats=stats)


class SuperuserModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_superuser

    def inaccessible_callback(self, name, **kwargs):
        abort(403)


class UserAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "username": "Имя пользователя",
        "is_superuser": "Суперпользователь",
        "is_admin": "Администратор",
    }
    column_formatters = {
        "is_superuser": lambda view, context, model, name: (
            "Да" if getattr(model, name) else "Нет"
        ),
        "is_admin": lambda view, context, model, name: (
            "Да" if getattr(model, name) else "Нет"
        ),
    }
    column_list = ("id", "username", "is_superuser", "is_admin")
    column_searchable_list = ("username",)
    column_default_sort = ("username", True)
    column_filters = ("is_superuser", "is_admin")
    column_sortable_list = ("id", "username", "is_superuser", "is_admin")
    form_columns = ("is_admin", "is_superuser")
    can_create = False
    can_delete = True
    action_disallowed_list = ("delete",)

    # Защита от удаления собственной учётной записи
    def delete_model(self, model):
        if model.id == current_user.id:
            flash(
                "Нельзя удалить собственную учётную запись.",
                "warning",
            )
            return False

        return super().delete_model(model)

    # Защита от снятия с себя прав суперпользователя
    def update_model(self, form, model):
        if model.id == current_user.id and not form.is_superuser.data:
            flash(
                "Нельзя снять с себя права суперпользователя.",
                "warning",
            )
            return False

        return super().update_model(form, model)


class CategoryAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "name": "Название",
        "slug": "Техническое название",
        "order": "Порядок",
        "template": "Шаблон",
    }
    column_list = (
        "id",
        "name",
        "slug",
        "order",
        "template",
    )
    column_searchable_list = ("name",)
    column_default_sort = ("id", False)
    column_editable_list = ("order",)
    form_columns = (
        "name",
        "slug",
        "order",
        "template",
    )


class TemplateVariableAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "name": "Техническое имя",
        "label": "Имя",
        "field_type": "Тип поля",
        "required": "Обязательно",
        "order": "Порядок",
        "category.name": "Категория",
    }
    column_formatters = {
        "required": lambda view, context, model, name: (
            "Да" if getattr(model, name) else "Нет"
        ),
    }
    column_list = ("label", "name", "field_type", "required", "category.name")
    column_searchable_list = ("name",)
    column_default_sort = ("name", False)
    column_filters = ("category.name",)
    form_columns = (
        "name",
        "label",
        "field_type",
        "required",
        "order",
        "category",
    )


class VariableOptionAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "value": "Значение",
        "output_value": "Отображаемое значение",
        "variable.label": "Шаблонная переменная",
    }
    column_list = ("id", "value", "output_value", "variable.label")
    column_searchable_list = ("value", "output_value", "variable.label")
    column_default_sort = ("id", False)
    column_filters = ("id", "value", "output_value")
    column_sortable_list = ("variable.label",)
    form_columns = (
        "value",
        "output_value",
        "variable",
    )


class DiaryAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "created_at": "Создан",
        "user.username": "Пользователь",
    }
    column_list = ("id", "created_at", "user.username")
    column_default_sort = ("id", False)
    form_columns = ("created_at",)
    can_create = False
    can_delete = True


class TherapyPurposeAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "name": "Название цели терапии",
        "output_value": "Отображаемое значение",
        "medications": "Препараты",
    }
    column_list = ("id", "name", "output_value")
    column_searchable_list = ("name", "output_value")
    column_default_sort = ("name", False)
    column_sortable_list = ("id", "name", "output_value")
    form_columns = (
        "name",
        "output_value",
        "medications",
    )
    action_disallowed_list = ("delete",)

    # Защита от удаления используемой цели терапии
    def delete_model(self, model):
        if is_purpose_used(model.id):
            flash(
                "Нельзя удалить цель терапии, которая используется в дневнике.",
                "warning",
            )
            return False

        return super().delete_model(model)


class TherapyMedicationAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "name": "Название препарата",
        "purposes": "Цели терапии",
    }
    column_list = ("id", "name", "purposes")
    column_searchable_list = ("name",)
    column_default_sort = ("name", False)
    column_sortable_list = ("id", "name")
    column_filters = ("purposes.name",)
    form_columns = (
        "name",
        "purposes",
    )
    action_disallowed_list = ("delete",)

    # Защита от удаления используемого препарата
    def delete_model(self, model):
        if is_medication_used(model.id):
            flash(
                "Нельзя удалить препарат, который используется в дневнике.",
                "warning",
            )
            return False

        return super().delete_model(model)


class TherapySourceAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "name": "Название группы параметров",
    }
    column_list = ("id", "name")
    column_searchable_list = ("name",)
    column_default_sort = ("id", False)
    form_columns = ("name",)


class TherapySourceValueAdmin(SuperuserModelView):
    column_labels = {
        "id": "ID",
        "name": "Название значения параметра",
        "source.name": "Группа параметров",
    }
    column_list = ("id", "name", "source.name")
    column_searchable_list = ("name", "source.name")
    column_default_sort = ("id", False)
    column_filters = ("id", "name", "source.name")
    column_sortable_list = ("source.name",)
    form_columns = (
        "name",
        "source",
    )


def init_admin(app):
    admin = Admin(
        index_view=SuperuserAdminIndexView(),
    )

    admin.add_view(UserAdmin(User, db, name="Пользователи"))
    admin.add_view(CategoryAdmin(Category, db, name="Категории"))
    admin.add_view(TemplateVariableAdmin(TemplateVariable, db, name="Переменные"))
    admin.add_view(VariableOptionAdmin(VariableOption, db, name="Опции"))
    admin.add_view(DiaryAdmin(Diary, db, name="Дневники"))
    admin.add_view(TherapyPurposeAdmin(TherapyPurpose, db, name="Цели терапии"))
    admin.add_view(TherapyMedicationAdmin(TherapyMedication, db, name="Препараты"))
    admin.add_view(
        TherapySourceAdmin(TherapySource, db, name="Группы параметров терапии")
    )
    admin.add_view(
        TherapySourceValueAdmin(
            TherapySourceValue, db, name="Значения параметров терапии"
        )
    )

    admin.init_app(app)
