from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from flask_wtf import FlaskForm

from app.extensions import db
from app.forms import TherapyPurposeForm, TherapyMedicationForm
from app.models import TherapyPurpose, TherapyGroup, TherapyMedication
from app.decorators import admin_required

therapy_bp = Blueprint("therapy", __name__)


# Список целей терапии
@therapy_bp.route("/therapy/purposes")
@login_required
@admin_required
def list_therapy_purposes():
    purposes = TherapyPurpose.query.order_by(
        TherapyPurpose.name,
    ).all()
    delete_form = FlaskForm()

    return render_template(
        "therapy/therapy_purposes.html",
        purposes=purposes,
        delete_form=delete_form,
    )


# Добавление цели терапии
@therapy_bp.route("/therapy/purposes/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_therapy_purpose():
    form = TherapyPurposeForm()

    if form.validate_on_submit():
        name = form.name.data.strip()

        existing_purpose = TherapyPurpose.query.filter_by(
            name=name,
        ).first()

        if existing_purpose:
            flash("Такая цель терапии уже существует.", "warning")

            return render_template(
                "therapy/add_therapy_purpose.html",
                form=form,
            )

        purpose = TherapyPurpose(
            name=name,
            output_value=form.output_value.data.strip(),
        )

        db.session.add(purpose)
        db.session.commit()

        flash("Цель терапии добавлена.", "success")
        return redirect(url_for("therapy.list_therapy_purposes"))

    return render_template(
        "therapy/add_therapy_purpose.html",
        form=form,
    )


# Редактирование цели терапии
@therapy_bp.route(
    "/therapy/purposes/<int:purpose_id>/edit",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit_therapy_purpose(purpose_id):
    purpose = TherapyPurpose.query.get_or_404(purpose_id)
    form = TherapyPurposeForm(obj=purpose)

    if form.validate_on_submit():
        name = form.name.data.strip()

        existing_purpose = TherapyPurpose.query.filter(
            TherapyPurpose.name == name,
            TherapyPurpose.id != purpose.id,
        ).first()

        if existing_purpose:
            flash("Такая цель терапии уже существует.", "warning")

            return render_template(
                "therapy/add_therapy_purpose.html",
                form=form,
                purpose=purpose,
            )

        purpose.name = name
        purpose.output_value = form.output_value.data.strip()

        db.session.commit()

        flash("Цель терапии успешно изменена.", "success")
        return redirect(url_for("therapy.list_therapy_purposes"))

    return render_template(
        "therapy/add_therapy_purpose.html",
        form=form,
        purpose=purpose,
    )


# Удаление цели терапии
@therapy_bp.route(
    "/therapy/purposes/<int:purpose_id>/delete",
    methods=["POST"],
)
@login_required
@admin_required
def delete_therapy_purpose(purpose_id):
    purpose = TherapyPurpose.query.get_or_404(purpose_id)

    therapy_group = TherapyGroup.query.filter_by(
        purpose_id=purpose.id,
    ).first()

    if therapy_group:
        flash(
            "Нельзя удалить цель терапии, которая используется в дневнике.",
            "warning",
        )
        return redirect(url_for("therapy.list_therapy_purposes"))

    db.session.delete(purpose)
    db.session.commit()

    flash("Цель терапии удалена.", "success")
    return redirect(url_for("therapy.list_therapy_purposes"))


# Список препаратов
@therapy_bp.route("/therapy/medications")
@login_required
@admin_required
def list_therapy_medications():
    medications = TherapyMedication.query.order_by(TherapyMedication.name).all()

    delete_form = FlaskForm()

    return render_template(
        "therapy/therapy_medications.html",
        medications=medications,
        delete_form=delete_form,
    )


# Добавление препарата
@therapy_bp.route("/therapy/medications/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_therapy_medication():
    form = TherapyMedicationForm()

    if form.validate_on_submit():
        name = form.name.data.strip()

        existing_medication = TherapyMedication.query.filter_by(
            name=name,
        ).first()

        if existing_medication:
            flash(
                "Такой препарат уже есть в справочнике.",
                "warning",
            )

            return render_template(
                "therapy/add_therapy_medication.html",
                form=form,
            )

        medication = TherapyMedication(name=name)

        db.session.add(medication)
        db.session.commit()

        flash("Препарат успешно добавлен.", "success")
        return redirect(url_for("therapy.list_therapy_medications"))

    return render_template(
        "therapy/add_therapy_medication.html",
        form=form,
    )


# Редактирование препарата
@therapy_bp.route(
    "/therapy/medications/<int:medication_id>/edit",
    methods=["GET", "POST"],
)
@login_required
@admin_required
def edit_therapy_medication(medication_id):
    medication = TherapyMedication.query.get_or_404(medication_id)
    form = TherapyMedicationForm(obj=medication)

    if form.validate_on_submit():
        name = form.name.data.strip()

        existing_medication = TherapyMedication.query.filter(
            TherapyMedication.name == name,
            TherapyMedication.id != medication.id,
        ).first()

        if existing_medication:
            flash(
                "Такой препарат уже есть в справочнике.",
                "warning",
            )

            return render_template(
                "therapy/add_therapy_medication.html",
                form=form,
                medication=medication,
            )

        medication.name = name

        db.session.commit()

        flash("Название препарата изменено.", "success")
        return redirect(url_for("therapy.list_therapy_medications"))

    return render_template(
        "therapy/add_therapy_medication.html",
        form=form,
        medication=medication,
    )


# Удаление препарата
@therapy_bp.route(
    "/therapy/medications/<int:medication_id>/delete",
    methods=["POST"],
)
@login_required
@admin_required
def delete_therapy_medication(medication_id):
    medication = TherapyMedication.query.get_or_404(medication_id)

    db.session.delete(medication)
    db.session.commit()

    flash("Препарат удалён из справочника.", "success")
    return redirect(url_for("therapy.list_therapy_medications"))
