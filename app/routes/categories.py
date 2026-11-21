from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from app.decorators import admin_required
from app.extensions import db
from app.forms import CategoryForm, TemplateVariableForm, VariableOptionForm
from app.models import (
    Category,
    TemplateVariable,
    VariableOption,
    DiaryEntry,
)

categories_bp = Blueprint("categories", __name__)


# Добавление категории / изменение шаблона
@categories_bp.route("/categories/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_category():
    form = CategoryForm()

    if form.validate_on_submit():
        last_order = db.session.query(db.func.max(Category.order)).scalar() or 0

        category = Category(
            name=form.name.data,
            slug=form.slug.data,
            order=last_order + 1,
            template=form.template.data,
        )

        db.session.add(category)
        db.session.commit()

        flash("Шаблон категории успешно сохранён.", "success")

        return redirect(url_for("categories.view_category", category_id=category.id))

    return render_template("categories/add_category.html", form=form)


# Редактирование категории
@categories_bp.route("/categories/edit/<int:category_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)

    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        category.name = form.name.data
        category.slug = form.slug.data
        category.template = form.template.data

        db.session.commit()

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
    category = Category.query.get_or_404(category_id)

    existing_entries = DiaryEntry.query.filter_by(
        category_id=category.id,
    ).first()

    if existing_entries:
        flash(
            "Нельзя удалить категорию, которая используется в дневниках.",
            "warning",
        )
        return redirect(url_for("categories.list_categories"))

    db.session.delete(category)
    db.session.commit()

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
    category = Category.query.get_or_404(category_id)
    form = TemplateVariableForm()

    if form.validate_on_submit():
        variable = TemplateVariable(
            category_id=category.id,
            name=form.name.data,
            label=form.label.data,
            field_type=form.field_type.data,
            required=form.required.data,
        )

        db.session.add(variable)
        db.session.commit()

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
    variable = TemplateVariable.query.get_or_404(variable_id)
    form = TemplateVariableForm(obj=variable)

    if form.validate_on_submit():
        variable.name = form.name.data
        variable.label = form.label.data
        variable.field_type = form.field_type.data
        variable.required = form.required.data

        db.session.commit()

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
    variable = TemplateVariable.query.get_or_404(variable_id)

    category_id = variable.category_id

    db.session.delete(variable)
    db.session.commit()

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
    variable = TemplateVariable.query.get_or_404(variable_id)
    form = VariableOptionForm()

    if form.validate_on_submit():
        option = VariableOption(
            variable_id=variable.id,
            value=form.value.data,
            output_value=form.output_value.data,
        )

        db.session.add(option)
        db.session.commit()

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
    variable = TemplateVariable.query.get_or_404(variable_id)

    option = VariableOption.query.filter_by(
        id=option_id,
        variable_id=variable_id,
    ).first_or_404()

    form = VariableOptionForm(obj=option)

    if form.validate_on_submit():
        option.value = form.value.data
        option.output_value = form.output_value.data

        db.session.commit()

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
    variable = TemplateVariable.query.get_or_404(variable_id)

    option = VariableOption.query.filter_by(
        id=option_id,
        variable_id=variable_id,
    ).first_or_404()

    db.session.delete(option)
    db.session.commit()

    flash("Вариант удалён.", "success")
    return redirect(url_for("categories.list_options", variable_id=variable.id))


# Список категорий
@categories_bp.route("/categories")
@login_required
@admin_required
def list_categories():
    categories = Category.query.order_by(Category.order).all()

    return render_template(
        "categories/list_categories.html",
        categories=categories,
    )


# Просмотр категории
@categories_bp.route("/categories/<int:category_id>")
@login_required
@admin_required
def view_category(category_id):
    category = Category.query.get_or_404(category_id)

    variables = (
        TemplateVariable.query.filter_by(category_id=category.id)
        .order_by(TemplateVariable.id)
        .all()
    )

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
    variable = TemplateVariable.query.get_or_404(variable_id)

    options = (
        VariableOption.query.filter_by(variable_id=variable_id)
        .order_by(VariableOption.value)
        .all()
    )
    return render_template(
        "categories/list_options.html",
        options=options,
        variable=variable,
    )
