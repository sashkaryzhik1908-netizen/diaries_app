from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db, login_manager
from app.forms import EditUserForm, LoginForm, RegisterForm
from app.models import User
from app.services.auth_service import (
    authenticate_user,
    create_user,
    delete_user,
    get_user_by_username,
    get_user_diaries,
    update_user,
)

auth_bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Регистрация
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))
    if form.validate_on_submit():
        username = form.username.data
        name = form.name.data
        password = form.password.data

        existing_user = get_user_by_username(username)

        if existing_user:
            flash("Такое имя пользователя уже занято.", "warning")
            return render_template("auth/register.html", form=form)

        user = create_user(username, name, password)

        login_user(user)

        flash("Регистрация успешно завершена.", "success")
        return redirect(url_for("auth.index"))

    return render_template("auth/register.html", form=form)


# Редактирование профиля
@auth_bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit_user():
    user = current_user
    form = EditUserForm(obj=user)

    if form.validate_on_submit():
        success = update_user(
            user=user,
            username=form.username.data,
            name=form.name.data,
            password=form.password.data,
        )

        if not success:
            flash("Это имя пользователя уже занято.", "danger")
            return render_template("auth/edit_user.html", form=form)

        flash("Данные профиля успешно обновлены.", "success")
        return redirect(url_for("auth.user"))

    return render_template("auth/edit_user.html", form=form)


# Удаление аккаунта
@auth_bp.route("/delete", methods=["POST"])
@login_required
def del_user():
    user = current_user._get_current_object()

    # Защита учётной записи суперпользователя
    if user.is_superuser:
        flash(
            "Нельзя удалить учётную запись суперпользователя.",
            "warning",
        )
        return redirect(url_for("auth.user"))

    delete_user(user)
    logout_user()

    flash("Профиль удалён", "success")
    return redirect(url_for("auth.index"))


# Вход
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = authenticate_user(username, password)

        if user:
            login_user(user)
            flash("Вы успешно вошли в систему.", "success")
            return redirect(url_for("auth.index"))

        flash("Неверное имя пользователя или пароль.", "danger")

    return render_template("auth/login.html", form=form)


# Выход
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("auth.index"))


# Главная страница
@auth_bp.route("/")
def index():
    return render_template("index.html")


# Личный кабинет
@auth_bp.route("/user")
@login_required
def user():
    diaries = get_user_diaries(current_user.id)
    return render_template(
        "auth/user.html",
        user=current_user,
        diaries=diaries,
    )
