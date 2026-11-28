from datetime import UTC, datetime

from app.extensions import db


class LaboratorySource(db.Model):
    """Исходный текст лабораторных исследований."""

    __tablename__ = "laboratory_source"

    id = db.Column(db.Integer, primary_key=True)

    diary_id = db.Column(
        db.Integer,
        db.ForeignKey("diary.id"),
        nullable=False,
        unique=True,
    )

    source_text = db.Column(db.Text, nullable=False)
    result_text = db.Column(db.Text, nullable=False, default="")

    ai_conclusion = db.Column(
        db.Text,
        nullable=False,
        default="",
        server_default="",
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    diary = db.relationship(
        "Diary",
        back_populates="laboratory_source",
    )

    def __repr__(self):
        return f"<LaboratorySource {self.id}>"


class LaboratoryCategory(db.Model):
    """Категории лабораторных исследований."""

    __tablename__ = "laboratory_category"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)

    indicators = db.relationship(
        "LaboratoryIndicator",
        backref="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<LaboratoryCategory {self.name}>"


class LaboratoryIndicator(db.Model):
    """Справочник лабораторных показателей."""

    __tablename__ = "laboratory_indicator"

    id = db.Column(db.Integer, primary_key=True)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("laboratory_category.id"),
        nullable=False,
    )

    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(50), nullable=True)
    unit = db.Column(db.String(50), nullable=True)

    precision = db.Column(db.Integer, nullable=True)

    aliases = db.relationship(
        "LaboratoryAlias",
        backref="indicator",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<LaboratoryIndicator {self.name}>"


class LaboratoryAlias(db.Model):
    """Альтернативные названия лабораторных показателей."""

    __tablename__ = "laboratory_alias"

    id = db.Column(db.Integer, primary_key=True)

    indicator_id = db.Column(
        db.Integer,
        db.ForeignKey("laboratory_indicator.id"),
        nullable=False,
    )

    alias = db.Column(db.String(150), nullable=False, unique=True)

    def __repr__(self):
        return f"<LaboratoryAlias {self.alias}>"
