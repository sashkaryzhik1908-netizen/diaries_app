from datetime import UTC, datetime

from flask_login import UserMixin

from app.extensions import db

# __Связь моделей целей терапии и препаратов__
therapy_purpose_medication = db.Table(
    "therapy_purpose_medication",
    db.Column(
        "purpose_id",
        db.Integer,
        db.ForeignKey("therapy_purpose.id"),
        primary_key=True,
    ),
    db.Column(
        "medication_id",
        db.Integer,
        db.ForeignKey("therapy_medication.id"),
        primary_key=True,
    ),
)


# ___модели___
class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), default="Врачев В.В")
    password = db.Column(db.String(500), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_superuser = db.Column(db.Boolean, default=False, nullable=False)
    diaries = db.relationship(
        "Diary",
        backref="user",
        cascade="all, delete-orphan",
    )


class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    order = db.Column(db.Integer, nullable=False)
    template = db.Column(db.Text, nullable=False)

    variables = db.relationship(
        "TemplateVariable",
        backref="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"{self.name}"


class TemplateVariable(db.Model):
    __tablename__ = "template_variable"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id"),
        nullable=False,
    )
    name = db.Column(db.String(100), nullable=False)
    label = db.Column(db.String(150), nullable=False)
    field_type = db.Column(db.String(30), nullable=False)
    required = db.Column(db.Boolean, default=False, nullable=False)
    order = db.Column(db.Integer, nullable=True, default=1)

    options = db.relationship(
        "VariableOption",
        backref="variable",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "category_id",
            "name",
            name="unique_category_variable",
        ),
    )

    def __repr__(self):
        return f"{self.label}"


class VariableOption(db.Model):
    __tablename__ = "variable_option"

    id = db.Column(db.Integer, primary_key=True)
    variable_id = db.Column(
        db.Integer,
        db.ForeignKey("template_variable.id"),
        nullable=False,
    )
    value = db.Column(db.String(255), nullable=False)
    output_value = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"{self.output_value}"


class Diary(db.Model):
    __tablename__ = "diary"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
    )

    number = db.Column(db.Integer, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    entries = db.relationship(
        "DiaryEntry",
        backref="diary",
        cascade="all, delete-orphan",
        order_by="DiaryEntry.category_id",
    )

    laboratory_source = db.relationship(
        "LaboratorySource",
        back_populates="diary",
        uselist=False,
        cascade="all, delete-orphan",
    )

    instrumental_source = db.relationship(
        "InstrumentalSource",
        back_populates="diary",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "number",
            name="unique_user_diary_number",
        ),
    )


class DiaryEntry(db.Model):
    __tablename__ = "diary_entry"

    id = db.Column(db.Integer, primary_key=True)

    diary_id = db.Column(
        db.Integer,
        db.ForeignKey("diary.id"),
        nullable=False,
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id"),
        nullable=False,
    )

    text = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    syndromes = db.Column(db.Text, nullable=False, default="")
    form_data = db.Column(db.Text, nullable=False, default="{}")

    category = db.relationship("Category")

    __table_args__ = (
        db.UniqueConstraint(
            "diary_id",
            "category_id",
            name="unique_diary_category",
        ),
    )


class TherapyPurpose(db.Model):
    """Цели терапии"""

    __tablename__ = "therapy_purpose"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    output_value = db.Column(db.String(200), nullable=False)
    medications = db.relationship(
        "TherapyMedication",
        secondary=therapy_purpose_medication,
        back_populates="purposes",
    )

    def __str__(self):
        return f"{self.name}"


class TherapyMedication(db.Model):
    """Справочник препаратов."""

    __tablename__ = "therapy_medication"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    purposes = db.relationship(
        "TherapyPurpose",
        secondary=therapy_purpose_medication,
        back_populates="medications",
    )

    def __str__(self):
        return f"{self.name}"


# Режим
# Диета
# Режим восполнения
# Единицы измерения
# Способы введения
# Кратность


class TherapySource(db.Model):
    """Справочник групп дополнительных параметров терапии."""

    __tablename__ = "therapy_source"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)

    values = db.relationship(
        "TherapySourceValue",
        back_populates="source",
        cascade="all, delete-orphan",
    )

    def __str__(self):
        return f"{self.name}"


class TherapySourceValue(db.Model):
    """Справочник значений дополнительных параметров терапии."""

    __tablename__ = "therapy_source_value"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

    source_id = db.Column(
        db.Integer,
        db.ForeignKey("therapy_source.id"),
        nullable=False,
    )
    source = db.relationship(
        "TherapySource",
        back_populates="values",
    )

    def __str__(self):
        return f"{self.name}"
