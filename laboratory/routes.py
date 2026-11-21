from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.decorators import admin_required

from app.models import Diary

from laboratory.models import (
    LaboratorySource,
    LaboratoryCategory,
    LaboratoryIndicator,
    LaboratoryAlias,
)

from laboratory.forms import (
    LaboratorySourceForm,
    LaboratoryCategoryForm,
    LaboratoryIndicatorForm,
    LaboratoryAliasForm,
)

from laboratory.services import generate_laboratory_text

laboratory_bp = Blueprint(
    "laboratory",
    __name__,
    template_folder="templates",
)


# ==========================================================
# КАТЕГОРИИ ЛАБОРАТОРНЫХ ИССЛЕДОВАНИЙ
# ==========================================================


@laboratory_bp.route("/laboratory/categories")
@login_required
@admin_required
def list_categories():
    """Список категорий лабораторных исследований."""
    categories = LaboratoryCategory.query.order_by(LaboratoryCategory.name).all()

    return render_template(
        "laboratory/list_categories.html",
        categories=categories,
    )


@laboratory_bp.route("/laboratory/categories/<int:category_id>")
@login_required
@admin_required
def view_category(category_id):
    """Просмотр категории и её показателей."""
    category = LaboratoryCategory.query.get_or_404(category_id)

    indicators = (
        LaboratoryIndicator.query.filter_by(category_id=category.id)
        .order_by(LaboratoryIndicator.name)
        .all()
    )

    return render_template(
        "laboratory/view_category.html",
        category=category,
        indicators=indicators,
    )


@laboratory_bp.route("/laboratory/categories/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_category():
    """Добавление категории лабораторных исследований."""
    form = LaboratoryCategoryForm()

    if form.validate_on_submit():
        category = LaboratoryCategory(
            name=form.name.data,
            slug=form.slug.data,
        )

        db.session.add(category)
        db.session.commit()

        flash("Категория добавлена.", "success")

        return redirect(
            url_for(
                "laboratory.view_category",
                category_id=category.id,
            )
        )

    return render_template(
        "laboratory/add_category.html",
        form=form,
    )


@laboratory_bp.route(
    "/laboratory/categories/edit/<int:category_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit_category(category_id):
    """Редактирование категории лабораторных исследований."""
    category = LaboratoryCategory.query.get_or_404(category_id)
    form = LaboratoryCategoryForm(obj=category)

    if form.validate_on_submit():
        category.name = form.name.data
        category.slug = form.slug.data

        db.session.commit()

        flash("Категория изменена.", "success")

        return redirect(
            url_for(
                "laboratory.view_category",
                category_id=category.id,
            )
        )

    return render_template(
        "laboratory/add_category.html",
        form=form,
        category=category,
    )


@laboratory_bp.route(
    "/laboratory/categories/delete/<int:category_id>",
    methods=["POST"],
)
@login_required
@admin_required
def delete_category(category_id):
    """Удаление категории лабораторных исследований."""
    category = LaboratoryCategory.query.get_or_404(category_id)

    db.session.delete(category)
    db.session.commit()

    flash("Категория удалена.", "success")

    return redirect(url_for("laboratory.list_categories"))


# ==========================================================
# ЛАБОРАТОРНЫЕ ПОКАЗАТЕЛИ
# ==========================================================


@laboratory_bp.route(
    "/laboratory/indicators/add/<int:category_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def add_indicator(category_id):
    """Добавление лабораторного показателя."""
    category = LaboratoryCategory.query.get_or_404(category_id)
    form = LaboratoryIndicatorForm()

    categories = LaboratoryCategory.query.order_by(LaboratoryCategory.name).all()

    form.category_id.choices = [(item.id, item.name) for item in categories]

    if form.validate_on_submit():
        indicator = LaboratoryIndicator(
            category_id=category.id,
            name=form.name.data,
            code=form.code.data or None,
            unit=form.unit.data or None,
            precision=form.precision.data,
        )

        db.session.add(indicator)
        db.session.commit()

        flash("Показатель добавлен.", "success")

        return redirect(
            url_for(
                "laboratory.view_category",
                category_id=category.id,
            )
        )

    if not form.is_submitted():
        form.category_id.data = category.id

    return render_template(
        "laboratory/add_indicator.html",
        form=form,
        category=category,
    )


@laboratory_bp.route(
    "/laboratory/indicators/edit/<int:indicator_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit_indicator(indicator_id):
    """Редактирование лабораторного показателя."""
    indicator = LaboratoryIndicator.query.get_or_404(indicator_id)
    form = LaboratoryIndicatorForm(obj=indicator)

    categories = LaboratoryCategory.query.order_by(LaboratoryCategory.name).all()

    form.category_id.choices = [(item.id, item.name) for item in categories]

    if form.validate_on_submit():
        indicator.category_id = form.category_id.data
        indicator.name = form.name.data
        indicator.code = form.code.data or None
        indicator.unit = form.unit.data or None
        indicator.precision = form.precision.data

        category_id = indicator.category_id

        db.session.commit()

        flash("Показатель изменён.", "success")

        return redirect(
            url_for(
                "laboratory.view_category",
                category_id=category_id,
            )
        )

    return render_template(
        "laboratory/add_indicator.html",
        form=form,
        indicator=indicator,
    )


@laboratory_bp.route(
    "/laboratory/indicators/delete/<int:indicator_id>",
    methods=["POST"],
)
@login_required
@admin_required
def delete_indicator(indicator_id):
    """Удаление лабораторного показателя."""
    indicator = LaboratoryIndicator.query.get_or_404(indicator_id)
    category_id = indicator.category_id

    db.session.delete(indicator)
    db.session.commit()

    flash("Показатель удалён.", "success")

    return redirect(
        url_for(
            "laboratory.view_category",
            category_id=category_id,
        )
    )


# ==========================================================
# АЛЬТЕРНАТИВНЫЕ НАЗВАНИЯ ПОКАЗАТЕЛЕЙ
# ==========================================================


@laboratory_bp.route(
    "/laboratory/aliases/<int:indicator_id>",
)
@login_required
@admin_required
def list_aliases(indicator_id):
    """Список альтернативных названий показателя."""
    indicator = LaboratoryIndicator.query.get_or_404(indicator_id)

    aliases = (
        LaboratoryAlias.query.filter_by(indicator_id=indicator.id)
        .order_by(LaboratoryAlias.alias)
        .all()
    )

    return render_template(
        "laboratory/list_aliases.html",
        indicator=indicator,
        aliases=aliases,
    )


@laboratory_bp.route(
    "/laboratory/aliases/add/<int:indicator_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def add_alias(indicator_id):
    """Добавление альтернативного названия показателя."""
    indicator = LaboratoryIndicator.query.get_or_404(indicator_id)
    form = LaboratoryAliasForm()

    indicators = LaboratoryIndicator.query.order_by(LaboratoryIndicator.name).all()

    form.indicator_id.choices = [(item.id, item.name) for item in indicators]

    if form.validate_on_submit():
        alias = LaboratoryAlias(
            indicator_id=indicator.id,
            alias=form.alias.data,
        )

        db.session.add(alias)
        db.session.commit()

        flash("Альтернативное название добавлено.", "success")

        return redirect(
            url_for(
                "laboratory.list_aliases",
                indicator_id=indicator.id,
            )
        )

    if not form.is_submitted():
        form.indicator_id.data = indicator.id

    return render_template(
        "laboratory/add_alias.html",
        form=form,
        indicator=indicator,
    )


@laboratory_bp.route(
    "/laboratory/aliases/edit/<int:alias_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit_alias(alias_id):
    """Редактирование альтернативного названия показателя."""
    alias = LaboratoryAlias.query.get_or_404(alias_id)
    form = LaboratoryAliasForm(obj=alias)

    indicators = LaboratoryIndicator.query.order_by(LaboratoryIndicator.name).all()

    form.indicator_id.choices = [(item.id, item.name) for item in indicators]

    if form.validate_on_submit():
        target_indicator = LaboratoryIndicator.query.get_or_404(form.indicator_id.data)

        alias.indicator_id = target_indicator.id
        alias.alias = form.alias.data

        db.session.commit()

        flash("Альтернативное название изменено.", "success")

        return redirect(
            url_for(
                "laboratory.list_aliases",
                indicator_id=target_indicator.id,
            )
        )

    return render_template(
        "laboratory/add_alias.html",
        form=form,
        alias=alias,
    )


@laboratory_bp.route(
    "/laboratory/aliases/delete/<int:alias_id>",
    methods=["POST"],
)
@login_required
@admin_required
def delete_alias(alias_id):
    """Удаление альтернативного названия показателя."""
    alias = LaboratoryAlias.query.get_or_404(alias_id)
    indicator_id = alias.indicator_id

    db.session.delete(alias)
    db.session.commit()

    flash("Альтернативное название удалено.", "success")

    return redirect(
        url_for(
            "laboratory.list_aliases",
            indicator_id=indicator_id,
        )
    )


# ==========================================================
# ИСХОДНЫЙ ТЕКСТ ЛАБОРАТОРНЫХ ИССЛЕДОВАНИЙ
# ==========================================================


@laboratory_bp.route(
    "/laboratory/diary/<int:diary_id>",
    methods=["GET", "POST"],
)
@login_required
def diary_laboratory(diary_id):
    """Заполнение лабораторных исследований для дневника."""

    diary = Diary.query.filter_by(
        id=diary_id,
        user_id=current_user.id,
    ).first_or_404()

    source = diary.laboratory_source

    form = LaboratorySourceForm()

    if form.validate_on_submit():
        source_text = form.source_text.data

        # Формирование обработанного лабораторного текста.
        result_text = generate_laboratory_text(source_text)

        if source is None:
            source = LaboratorySource(
                diary_id=diary.id,
                source_text=source_text,
                result_text=result_text,
            )

            db.session.add(source)

        else:
            source.source_text = source_text
            source.result_text = result_text

        try:
            db.session.commit()
            flash("Лабораторный текст сохранён.", "success")

        except Exception:
            db.session.rollback()
            current_app.logger.exception("Ошибка при сохранении лабораторного текста.")
            flash("Не удалось сохранить лабораторный текст.", "danger")

        return redirect(
            url_for(
                "diaries.view_diary",
                diary_id=diary.id,
            )
        )

    if source is not None:
        form.source_text.data = source.source_text

    return render_template(
        "laboratory/diary_source.html",
        form=form,
        diary=diary,
        source=source,
    )
