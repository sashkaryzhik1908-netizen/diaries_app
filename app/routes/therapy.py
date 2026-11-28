from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectChoice

from app.decorators import admin_required
from app.extensions import db
from app.forms import TherapyMedicationForm, TherapyPurposeForm
from app.models import TherapyMedication, TherapyPurpose
from app.services import therapy_service

therapy_bp = Blueprint("therapy", __name__)


# Список целей терапии
@therapy_bp.route("/therapy/purposes")
@login_required
@admin_required
def list_therapy_purposes():
    purposes = therapy_service.get_therapy_purposes()

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
        output_value = form.output_value.data.strip()

        existing_purpose = therapy_service.get_existing_purpose(name)

        if existing_purpose:
            flash("Такая цель терапии уже существует.", "warning")

            return render_template(
                "therapy/add_therapy_purpose.html",
                form=form,
            )

        therapy_service.create_therapy_purpose(
            name=name,
            output_value=output_value,
        )

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
    purpose = db.get_or_404(TherapyPurpose, purpose_id)

    form = TherapyPurposeForm(obj=purpose)

    if form.validate_on_submit():
        name = form.name.data.strip()
        output_value = form.output_value.data.strip()

        existing_purpose = therapy_service.get_existing_purpose(
            name,
            exclude_id=purpose.id,
        )

        if existing_purpose:
            flash("Такая цель терапии уже существует.", "warning")

            return render_template(
                "therapy/add_therapy_purpose.html",
                form=form,
                purpose=purpose,
            )

        therapy_service.update_therapy_purpose(
            purpose=purpose,
            name=name,
            output_value=output_value,
        )

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
    purpose = db.get_or_404(TherapyPurpose, purpose_id)

    if therapy_service.is_purpose_used(purpose.id):
        flash(
            "Нельзя удалить цель терапии, которая используется в дневнике.",
            "warning",
        )
        return redirect(url_for("therapy.list_therapy_purposes"))

    therapy_service.delete_therapy_purpose(purpose)

    flash("Цель терапии удалена.", "success")
    return redirect(url_for("therapy.list_therapy_purposes"))


# Список препаратов
@therapy_bp.route("/therapy/medications")
@login_required
@admin_required
def list_therapy_medications():
    medications = therapy_service.get_all_therapy_medications()

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
    form.purpose.choices = [
        SelectChoice(str(p.id), p.name) for p in therapy_service.get_therapy_purposes()
    ]
    if form.validate_on_submit():
        name = form.name.data.strip()
        purpose_ids, error = therapy_service.validate_purpose_ids(
            request.form.get("purpose_ids", "")
        )

        if error:
            flash(error, "warning")

            return render_template(
                "therapy/add_therapy_medication.html",
                form=form,
            )

        existing_medication = therapy_service.get_existing_medication(name)

        if existing_medication:
            flash(
                "Такой препарат уже есть в справочнике.",
                "warning",
            )

            return render_template(
                "therapy/add_therapy_medication.html",
                form=form,
            )

        therapy_service.create_therapy_medication(name, purpose_ids)

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
    medication = db.get_or_404(TherapyMedication, medication_id)

    form = TherapyMedicationForm(obj=medication)
    form.purpose.choices = [
        SelectChoice(str(p.id), p.name) for p in therapy_service.get_therapy_purposes()
    ]

    if request.method == "GET":
        form.purpose.data = [p.id for p in medication.purposes]

    if form.validate_on_submit():
        name = form.name.data.strip()
        purpose_ids, error = therapy_service.validate_purpose_ids(
            request.form.get("purpose_ids", "")
        )

        if error:
            flash(error, "warning")

            return render_template(
                "therapy/add_therapy_medication.html",
                form=form,
                medication=medication,
            )

        existing_medication = therapy_service.get_existing_medication(
            name,
            exclude_id=medication.id,
        )

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

        therapy_service.update_therapy_medication(
            medication=medication,
            name=name,
            purpose_ids=purpose_ids,
        )

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
    medication = db.get_or_404(TherapyMedication, medication_id)

    # Проверка использования препарата в дневниках
    if therapy_service.is_medication_used(medication.id):
        flash(
            "Нельзя удалить препарат, который используется в дневнике.",
            "warning",
        )
        return redirect(url_for("therapy.list_therapy_medications"))

    therapy_service.delete_therapy_medication(medication)

    flash("Препарат удалён из справочника.", "success")
    return redirect(url_for("therapy.list_therapy_medications"))
