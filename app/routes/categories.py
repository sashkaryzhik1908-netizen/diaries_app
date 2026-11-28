from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required
from sqlalchemy import select

from app.decorators import admin_required
from app.extensions import db
from app.forms import CategoryForm, TemplateVariableForm, VariableOptionForm
from app.models import Category, TemplateVariable, VariableOption
from app.services.categories_service import (
    create_category,
    create_option,
    create_variable,
    delete_category,
    delete_variable,
    update_category,
    update_option,
    update_variable,
)
from app.services.categories_service import (
    delete_option as delete_option_service,
)

categories_bp = Blueprint("categories", __name__)


# Добавление категории / изменение шаблона
@categories_bp.route("/categories/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_category():
    form = CategoryForm()

    if form.validate_on_submit():
        category = create_category(
            name=form.name.data,
            slug=form.slug.data,
            template=form.template.data,
            order=form.order.data,
        )

        flash("Шаблон категории успешно сохранён.", "success")

        return redirect(url_for("categories.view_category", category_id=category.id))

    return render_template("categories/add_category.html", form=form)


# Редактирование категории
@categories_bp.route("/categories/edit/<int:category_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_category(category_id):
    category = db.get_or_404(Category, category_id)

    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        update_category(
            category=category,
            name=form.name.data,
            slug=form.slug.data,
            template=form.template.data,
            order=form.order.data,
        )

        flash("Шаблон категории успешно изменён.", "success")

        return redirect(url_for("categories.view_category", category_id=category.id))

    return render_template(
        "categories/add_category.html",
        form=form,
        category=category,
    )


# Удаление категории
@categories_bp.route("/categories/delete/<int:category_id>", methods=["POST"])
@login_required
@admin_required
def del_category(category_id):
    category = db.get_or_404(Category, category_id)

    success = delete_category(category)

    if not success:
        flash(
            "Нельзя удалить категорию, которая используется в дневниках.",
            "warning",
        )
        return redirect(url_for("categories.list_categories"))

    flash("Категория удалена.", "success")

    return redirect(url_for("categories.list_categories"))


# Добавление переменной
@categories_bp.route(
    "/categories/<int:category_id>/add_variable",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def add_variable(category_id):
    category = db.get_or_404(Category, category_id)
    form = TemplateVariableForm()

    if form.validate_on_submit():
        create_variable(
            category_id=category.id,
            name=form.name.data,
            label=form.label.data,
            field_type=form.field_type.data,
            required=form.required.data,
            order=form.order.data,
        )

        flash("Переменная успешно добавлена.", "success")
        return redirect(url_for("categories.view_category", category_id=category.id))

    return render_template(
        "categories/add_variable.html",
        form=form,
        category=category,
    )


# Редактирование переменной
@categories_bp.route(
    "/categories/edit_variable/<int:variable_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit_variable(variable_id):
    variable = db.get_or_404(TemplateVariable, variable_id)
    form = TemplateVariableForm(obj=variable)

    if form.validate_on_submit():
        update_variable(
            variable=variable,
            name=form.name.data,
            label=form.label.data,
            field_type=form.field_type.data,
            required=form.required.data,
            order=form.order.data,
        )

        flash("Переменная успешно изменена.", "success")
        return redirect(
            url_for(
                "categories.view_category",
                category_id=variable.category_id,
            )
        )

    return render_template(
        "categories/add_variable.html",
        form=form,
        variable=variable,
    )


# Удаление переменной
@categories_bp.route(
    "/categories/del_variable/<int:variable_id>",
    methods=["POST"],
)
@login_required
@admin_required
def del_variable(variable_id):
    variable = db.get_or_404(TemplateVariable, variable_id)

    category_id = variable.category_id

    delete_variable(variable)

    flash("Переменная удалена.", "success")
    return redirect(url_for("categories.view_category", category_id=category_id))


# Добавление варианта
@categories_bp.route(
    "/variables/<int:variable_id>/add_option",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def add_option(variable_id):
    variable = db.get_or_404(TemplateVariable, variable_id)
    form = VariableOptionForm()

    if form.validate_on_submit():
        create_option(
            variable_id=variable.id,
            value=form.value.data,
            output_value=form.output_value.data,
        )

        flash("Вариант успешно добавлен.", "success")
        return redirect(
            url_for(
                "categories.view_category",
                category_id=variable.category_id,
            )
        )

    return render_template(
        "categories/add_option.html",
        form=form,
        variable=variable,
    )


# Редактирование варианта
@categories_bp.route(
    "/variables/<int:variable_id>/options/<int:option_id>/edit",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit_option(variable_id, option_id):
    variable = db.get_or_404(TemplateVariable, variable_id)

    option = db.first_or_404(
        select(VariableOption).where(
            VariableOption.id == option_id,
            VariableOption.variable_id == variable_id,
        )
    )

    form = VariableOptionForm(obj=option)

    if form.validate_on_submit():
        update_option(
            option=option,
            value=form.value.data,
            output_value=form.output_value.data,
        )

        flash("Вариант успешно изменён.", "success")
        return redirect(url_for("categories.list_options", variable_id=variable.id))

    return render_template(
        "categories/add_option.html",
        form=form,
        variable=variable,
        option=option,
    )


# Удаление варианта
@categories_bp.route(
    "/variables/<int:variable_id>/options/<int:option_id>/delete",
    methods=["POST"],
)
@login_required
@admin_required
def delete_option(variable_id, option_id):
    variable = db.get_or_404(TemplateVariable, variable_id)

    option = db.first_or_404(
        select(VariableOption).where(
            VariableOption.id == option_id,
            VariableOption.variable_id == variable_id,
        )
    )

    delete_option_service(option)

    flash("Вариант удалён.", "success")
    return redirect(url_for("categories.list_options", variable_id=variable.id))


# Список категорий
@categories_bp.route("/categories")
@login_required
@admin_required
def list_categories():
    categories = db.session.scalars(select(Category).order_by(Category.order)).all()

    return render_template(
        "categories/list_categories.html",
        categories=categories,
    )


# Просмотр категории
@categories_bp.route("/categories/<int:category_id>")
@login_required
@admin_required
def view_category(category_id):
    category = db.get_or_404(Category, category_id)

    variables = db.session.scalars(
        select(TemplateVariable)
        .where(TemplateVariable.category_id == category.id)
        .order_by(TemplateVariable.id)
    ).all()

    return render_template(
        "categories/view_category.html",
        category=category,
        variables=variables,
    )


# Список вариантов переменной
@categories_bp.route("/categories/<int:variable_id>/options")
@login_required
@admin_required
def list_options(variable_id):
    variable = db.get_or_404(TemplateVariable, variable_id)

    options = db.session.scalars(
        select(VariableOption)
        .where(VariableOption.variable_id == variable_id)
        .order_by(VariableOption.value)
    ).all()
    return render_template(
        "categories/list_options.html",
        options=options,
        variable=variable,
    )
