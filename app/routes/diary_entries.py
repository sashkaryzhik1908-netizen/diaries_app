import json

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.extensions import db
from app.services import therapy_service
from app.services.category_form_service import process_category_form
from app.services.diary_service import (
    create_diary_entry,
    generate_category_text,
    get_category,
    get_category_variables,
    get_diary_entry,
    get_diary_for_user,
    get_therapy_medications,
    get_therapy_purposes,
    get_therapy_source_values,
    get_therapy_sources,
    save_diary_entry,
    update_diary_entry,
)
from app.services.prescriptions_service import process_prescriptions

diary_entries_bp = Blueprint("diary_entries", __name__)


# Заполнение категории в дневнике
@diary_entries_bp.route(
    "/diaries/<int:diary_id>/categories/<int:category_id>/fill",
    methods=["GET", "POST"],
)
@login_required
def fill_category(diary_id, category_id):
    diary = get_diary_for_user(diary_id, current_user.id)

    category = get_category(category_id)

    entry = get_diary_entry(diary.id, category.id)

    # Загружаем ранее сохранённые данные формы
    try:
        form_data = json.loads(entry.form_data) if entry and entry.form_data else {}
    except (json.JSONDecodeError, TypeError):
        current_app.logger.exception("Ошибка чтения данных формы дневника.")
        form_data = {}

    values = {}
    errors = []
    generated_text = None

    variables = get_category_variables(category.id)

    if category.slug == "prescriptions":
        purposes = get_therapy_purposes()

        medications = get_therapy_medications()

        sources = get_therapy_sources()
        source_values = get_therapy_source_values()

        if category.slug == "prescriptions":
            purposes = get_therapy_purposes()

            medications = get_therapy_medications()

            sources = get_therapy_sources()
            source_values = get_therapy_source_values()

            # Проверка наличия обязательных справочников
            required_sources = (
                "Режим",
                "Диета",
                "Режим восполнения",
                "Единицы измерения",
                "Способы введения",
                "Кратность",
            )

            missing_sources = [name for name in required_sources if name not in sources]

            if missing_sources:
                for name in missing_sources:
                    flash(
                        f"Отсутствует обязательный справочник «{name}». "
                        "Обратитесь к администратору.",
                        "warning",
                    )

                return redirect(url_for("diaries.view_diary", diary_id=diary.id))

        else:
            purposes = []
            medications = []
            sources = {}
            source_values = []

    else:
        purposes = []
        medications = []
        sources = {}
        source_values = []

    if request.method == "POST":
        # Сохраняем все отправленные поля формы
        form_data = request.form.to_dict(flat=False)

        if category.slug == "prescriptions":
            generated_text, errors = process_prescriptions(request.form)

        else:
            values, errors = process_category_form(
                request.form,
                variables,
                category,
            )

        if not errors:
            if generated_text is None:
                generated_text = generate_category_text(category, values)

            syndromes = ", ".join(values.get("syndromes", []))

            if entry:
                entry = update_diary_entry(
                    entry=entry,
                    generated_text=generated_text,
                    syndromes=syndromes if category.slug == "condition" else "",
                    form_data=form_data,
                )

            else:
                entry = create_diary_entry(
                    diary_id=diary.id,
                    category_id=category.id,
                    generated_text=generated_text,
                    syndromes=syndromes if category.slug == "condition" else "",
                    form_data=form_data,
                )

            try:
                save_diary_entry()
            except Exception:
                db.session.rollback()
                current_app.logger.exception("Ошибка при сохранении раздела дневника.")
                flash(
                    "Произошла ошибка при сохранении раздела дневника.",
                    "danger",
                )
                return render_template(
                    "diares/fill_category.html",
                    category=category,
                    diary=diary,
                    values=values,
                    variables=variables,
                    errors=errors,
                    generated_text=generated_text,
                    purposes=purposes,
                    medications=medications,
                    sources=sources,
                    source_values=source_values,
                    form_data=form_data,
                )

            flash(
                "Раздел дневника успешно сохранён.",
                "success",
            )

            return redirect(url_for("diaries.view_diary", diary_id=diary.id))

        else:
            flash(
                "Не удалось сохранить раздел. Проверьте обязательные поля.",
                "warning",
            )

    return render_template(
        "diares/fill_category.html",
        category=category,
        diary=diary,
        values=values,
        variables=variables,
        errors=errors,
        generated_text=generated_text,
        purposes=purposes,
        medications=medications,
        sources=sources,
        source_values=source_values,
        form_data=form_data,
    )


# Получение препаратов по цели терапии
@diary_entries_bp.route("/therapy/medications/<int:purpose_id>")
@login_required
def get_medications_by_purpose(purpose_id):
    medications = therapy_service.get_therapy_medications(purpose_id)

    return jsonify(
        [{"id": medication.id, "name": medication.name} for medication in medications]
    )
