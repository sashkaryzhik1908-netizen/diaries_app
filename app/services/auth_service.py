from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import Diary, User


def get_user_by_username(username):
    return db.session.scalar(select(User).where(User.username == username))


def authenticate_user(username, password):
    user = get_user_by_username(username)

    if user and check_password_hash(user.password, password):
        return user

    return None


def create_user(username, name, password):
    user = User(
        username=username,
        name=name,
        password=generate_password_hash(password),
    )

    db.session.add(user)
    db.session.commit()

    return user


def update_user(user, username, name, password=None):
    existing_user = get_user_by_username(username)

    if existing_user and existing_user.id != user.id:
        return False

    user.username = username
    user.name = name

    if password:
        user.password = generate_password_hash(password)

    db.session.commit()

    return True


def delete_user(user):
    db.session.delete(user)
    db.session.commit()


def get_user_diaries(user_id):
    return db.session.scalars(select(Diary).where(Diary.user_id == user_id)).all()
