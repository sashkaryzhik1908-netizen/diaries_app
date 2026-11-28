from datetime import UTC, datetime

from app.extensions import db


class InstrumentalSource(db.Model):
    """Исходный текст инструментальных исследований."""

    __tablename__ = "instrumental_source"

    id = db.Column(db.Integer, primary_key=True)

    diary_id = db.Column(
        db.Integer,
        db.ForeignKey("diary.id"),
        nullable=False,
        unique=True,
    )

    source_text = db.Column(db.Text, nullable=False)
    result_text = db.Column(db.Text, nullable=False, default="")

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
        back_populates="instrumental_source",
    )

    def __repr__(self):
        return f"<InstrumentalSource {self.id}>"


class InstrumentalIndicator(db.Model):
    """Справочник инструментальных методов исследований."""

    __tablename__ = "instrumental_indicator"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)

    aliases = db.relationship(
        "InstrumentalAlias",
        backref="indicator",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"{self.name}"


class InstrumentalAlias(db.Model):
    """Альтернативные названия инструментальных исследований."""

    __tablename__ = "instrumental_alias"

    id = db.Column(db.Integer, primary_key=True)

    indicator_id = db.Column(
        db.Integer,
        db.ForeignKey("instrumental_indicator.id"),
        nullable=False,
    )

    alias = db.Column(db.String(200), nullable=False, unique=True)

    def __repr__(self):
        return f"{self.alias}"
