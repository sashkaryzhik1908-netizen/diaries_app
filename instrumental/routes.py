from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from app.decorators import admin_required
from app.extensions import db
from app.models import Diary
from instrumental import services as instrumental_service
from instrumental.forms import (
    InstrumentalAliasForm,
    InstrumentalIndicatorForm,
    InstrumentalSourceForm,
)
from instrumental.models import (
    InstrumentalAlias,
    InstrumentalIndicator,
)

instrumental_bp = Blueprint(
    "instrumental",
    __name__,
    template_folder="templates",
)


# ==========================================================
# ИНСТРУМЕНТАЛЬНЫЕ МЕТОДЫ
# ==========================================================


@instrumental_bp.route(
    "/instrumental/indicators",
)
@login_required
@admin_required
def list_indicators():
    """Список инструментальных методов."""
    indicators = db.session.scalars(
        select(InstrumentalIndicator).order_by(
            InstrumentalIndicator.name,
        )
    ).all()

    return render_template(
        "list_indicators.html",
        indicators=indicators,
    )


@instrumental_bp.route(
    "/instrumental/indicators/add",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def add_indicator():
    """Добавление инструментального метода."""

    form = InstrumentalIndicatorForm()

    if form.validate_on_submit():
        instrumental_service.create_instrumental_indicator(
            name=form.name.data,
        )

        flash("Метод добавлен.", "success")

        return redirect(
            url_for(
                "instrumental.list_indicators",
            )
        )

    return render_template(
        "add_indicator.html",
        form=form,
    )


@instrumental_bp.route(
    "/instrumental/indicators/edit/<int:indicator_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit_indicator(indicator_id):
    """Редактирование инструментального метода."""
    indicator = db.get_or_404(InstrumentalIndicator, indicator_id)
    form = InstrumentalIndicatorForm(obj=indicator)

    if form.validate_on_submit():
        instrumental_service.update_instrumental_indicator(
            indicator=indicator,
            name=form.name.data,
        )

        flash("Метод изменён.", "success")

        return redirect(
            url_for(
                "instrumental.list_indicators",
            )
        )

    return render_template(
        "add_indicator.html",
        form=form,
        indicator=indicator,
    )


@instrumental_bp.route(
    "/instrumental/indicators/delete/<int:indicator_id>",
    methods=["POST"],
)
@login_required
@admin_required
def delete_indicator(indicator_id):
    """Удаление инструментального метода"""
    indicator = db.get_or_404(InstrumentalIndicator, indicator_id)

    instrumental_service.delete_instrumental_indicator(indicator)

    flash("Метод удалён.", "success")

    return redirect(
        url_for(
            "instrumental.list_indicators",
        )
    )


# ==========================================================
# АЛЬТЕРНАТИВНЫЕ НАЗВАНИЯ МЕТОДОВ
# ==========================================================


@instrumental_bp.route(
    "/instrumental/aliases/<int:indicator_id>",
)
@login_required
@admin_required
def list_aliases(indicator_id):
    """Список альтернативных названий метода."""
    indicator = db.get_or_404(InstrumentalIndicator, indicator_id)

    aliases = instrumental_service.get_indicator_aliases(indicator.id)

    return render_template(
        "list_aliases.html",
        indicator=indicator,
        aliases=aliases,
    )


@instrumental_bp.route(
    "/instrumental/aliases/add/<int:indicator_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def add_alias(indicator_id):
    """Добавление альтернативного названия показателя."""
    indicator = db.get_or_404(InstrumentalIndicator, indicator_id)
    form = InstrumentalAliasForm()

    indicators = db.session.scalars(
        select(InstrumentalIndicator).order_by(InstrumentalIndicator.name)
    ).all()

    form.indicator_id.choices = [(item.id, item.name) for item in indicators]

    if form.validate_on_submit():
        instrumental_service.create_instrumental_alias(
            indicator_id=indicator.id,
            alias_text=form.alias.data,
        )

        flash("Альтернативное название добавлено.", "success")

        return redirect(
            url_for(
                "instrumental.list_aliases",
                indicator_id=indicator.id,
            )
        )

    if not form.is_submitted():
        form.indicator_id.data = indicator.id

    return render_template(
        "add_alias.html",
        form=form,
        indicator=indicator,
    )


@instrumental_bp.route(
    "/instrumental/aliases/edit/<int:alias_id>",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit_alias(alias_id):
    """Редактирование альтернативного названия показателя."""
    alias = db.get_or_404(InstrumentalAlias, alias_id)
    form = InstrumentalAliasForm(obj=alias)

    indicators = db.session.scalars(
        select(InstrumentalIndicator).order_by(InstrumentalIndicator.name)
    ).all()

    form.indicator_id.choices = [(item.id, item.name) for item in indicators]

    if form.validate_on_submit():
        target_indicator = db.get_or_404(
            InstrumentalIndicator,
            form.indicator_id.data,
        )

        instrumental_service.update_instrumental_alias(
            alias=alias,
            indicator_id=target_indicator.id,
            alias_text=form.alias.data,
        )

        flash("Альтернативное название изменено.", "success")

        return redirect(
            url_for(
                "instrumental.list_aliases",
                indicator_id=target_indicator.id,
            )
        )
    if not form.is_submitted():
        form.indicator_id.data = alias.indicator_id

    return render_template(
        "add_alias.html",
        form=form,
        alias=alias,
    )


@instrumental_bp.route(
    "/instrumental/aliases/delete/<int:alias_id>",
    methods=["POST"],
)
@login_required
@admin_required
def delete_alias(alias_id):
    """Удаление альтернативного названия показателя."""
    alias = db.get_or_404(InstrumentalAlias, alias_id)
    indicator_id = alias.indicator_id

    instrumental_service.delete_instrumental_alias(alias)

    flash("Альтернативное название удалено.", "success")

    return redirect(
        url_for(
            "instrumental.list_aliases",
            indicator_id=indicator_id,
        )
    )


# ==========================================================
# ИСХОДНЫЙ ТЕКСТ ИНСТРУМЕНТАЛЬНЫХ ИССЛЕДОВАНИЙ
# ==========================================================


@instrumental_bp.route(
    "/instrumental/diary/<int:diary_id>",
    methods=["GET", "POST"],
)
@login_required
def diary_instrumental(diary_id):
    """Заполнение инструментальных исследований для дневника."""

    diary = db.first_or_404(
        select(Diary).where(
            Diary.id == diary_id,
            Diary.user_id == current_user.id,
        )
    )

    source = diary.instrumental_source

    form = InstrumentalSourceForm()

    if form.validate_on_submit():
        source_text = form.source_text.data

        # Формирование обработанного текста.
        result_text = instrumental_service.generate_instrumental_text(source_text)

        try:
            instrumental_service.save_instrumental_source(
                diary_id=diary.id,
                source=source,
                source_text=source_text,
                result_text=result_text,
            )

            flash("Текст исследований сохранён.", "success")

        except Exception:
            db.session.rollback()
            current_app.logger.exception("Ошибка при сохранении  текста.")
            flash("Не удалось сохранить текст.", "danger")

        return redirect(
            url_for(
                "diaries.view_diary",
                diary_id=diary.id,
            )
        )

    if source is not None:
        form.source_text.data = source.source_text

    return render_template(
        "diary_source.html",
        form=form,
        diary=diary,
        source=source,
    )
