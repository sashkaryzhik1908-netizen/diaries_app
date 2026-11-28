from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user, login_required

from app.extensions import db
from app.services.diaries_service import (
    create_diary as create_diary_service,
)
from app.services.diaries_service import (
    delete_diary as delete_diary_service,
)
from app.services.diaries_service import (
    get_categories,
    get_diary,
    get_diary_entries,
    get_syndromes,
    get_user_diaries,
)

from laboratory.services import combine_laboratory_with_conclusions

diaries_bp = Blueprint("diaries", __name__)


# Список дневников
@diaries_bp.route("/diaries")
@login_required
def list_diaries():
    diaries = get_user_diaries(current_user.id)

    return render_template(
        "diares/diaries.html",
        diaries=diaries,
    )


# Создание дневника
@diaries_bp.route("/diaries/create", methods=["POST"])
@login_required
def create_diary():
    try:
        diary = create_diary_service(current_user.id)
        flash("Новый дневник создан.", "success")

        return redirect(url_for("diaries.view_diary", diary_id=diary.id))

    except Exception:
        db.session.rollback()

        current_app.logger.exception("Ошибка при создании дневника.")

        flash("Не удалось создать дневник.", "danger")

        return redirect(url_for("diaries.list_diaries"))


# Просмотр дневника
@diaries_bp.route("/diaries/<int:diary_id>")
@login_required
def view_diary(diary_id):
    diary = get_diary(diary_id, current_user.id)
    entries = get_diary_entries(diary.id)
    categories = get_categories()
    syndromes = get_syndromes(entries)

    laboratory_text = ""

    if diary.laboratory_source:
        laboratory_text = combine_laboratory_with_conclusions(
            result_text=diary.laboratory_source.result_text,
            ai_conclusion=diary.laboratory_source.ai_conclusion,
        )

    return render_template(
        "diares/view_diary.html",
        diary=diary,
        categories=categories,
        syndromes=syndromes,
        entries=entries,
        laboratory_text=laboratory_text,
    )


# Удаление дневника
@diaries_bp.route("/diaries/<int:diary_id>/delete", methods=["POST"])
@login_required
def delete_diary(diary_id):
    diary = get_diary(diary_id, current_user.id)

    try:
        delete_diary_service(diary)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Ошибка при удалении дневника.")
        flash("Не удалось удалить дневник.", "danger")
        return redirect(url_for("diaries.list_diaries"))

    flash("Дневник удалён.", "success")
    return redirect(url_for("diaries.list_diaries"))
