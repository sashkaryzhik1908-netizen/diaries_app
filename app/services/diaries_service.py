from sqlalchemy import func, select

from app.extensions import db
from app.models import Category, Diary, DiaryEntry


def get_user_diaries(user_id):
    return db.session.scalars(
        select(Diary).where(Diary.user_id == user_id).order_by(Diary.created_at.desc())
    ).all()


def create_diary(user_id):
    last_number = (
        db.session.scalar(
            select(func.max(Diary.number)).where(Diary.user_id == user_id)
        )
        or 0
    )

    diary = Diary(
        user_id=user_id,
        number=last_number + 1,
    )

    db.session.add(diary)
    db.session.commit()

    return diary


def get_diary(diary_id, user_id):
    return db.first_or_404(
        select(Diary).where(
            Diary.id == diary_id,
            Diary.user_id == user_id,
        )
    )


def get_diary_entries(diary_id):
    return db.session.scalars(
        select(DiaryEntry)
        .where(DiaryEntry.diary_id == diary_id)
        .join(Category, DiaryEntry.category_id == Category.id)
        .order_by(Category.order)
    ).all()


def get_categories():
    return db.session.scalars(select(Category).order_by(Category.order)).all()


def get_syndromes(entries):
    condition_entry = next(
        (entry for entry in entries if entry.category.slug == "condition"),
        None,
    )

    return (
        condition_entry.syndromes.split(", ")
        if condition_entry and condition_entry.syndromes
        else []
    )


def delete_diary(diary):
    db.session.delete(diary)
    db.session.commit()
