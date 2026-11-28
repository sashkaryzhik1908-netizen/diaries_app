from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class LaboratoryCategoryForm(FlaskForm):
    """Форма категории лабораторных исследований."""

    name = StringField(
        "Название категории",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    slug = StringField(
        "Техническое название категории",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    submit = SubmitField("Сохранить")


class LaboratoryIndicatorForm(FlaskForm):
    """Форма лабораторного показателя."""

    category_id = SelectField(
        "Категория исследования",
        coerce=int,
        validators=[DataRequired()],
    )
    name = StringField(
        "Название показателя",
        validators=[
            DataRequired(),
            Length(max=150),
        ],
    )
    code = StringField(
        "Код показателя",
        validators=[Length(max=50)],
    )
    unit = StringField(
        "Единица измерения",
        validators=[Length(max=50)],
    )
    precision = IntegerField(
        "Количество знаков после запятой",
        validators=[Optional(), NumberRange(min=0, max=6)],
    )
    submit = SubmitField("Сохранить")


class LaboratoryAliasForm(FlaskForm):
    """Форма альтернативного названия показателя."""

    indicator_id = SelectField(
        "Лабораторный показатель",
        coerce=int,
        validators=[DataRequired()],
    )
    alias = StringField(
        "Альтернативное название",
        validators=[
            DataRequired(),
            Length(max=150),
        ],
    )
    submit = SubmitField("Сохранить")


class LaboratorySourceForm(FlaskForm):
    """Форма исходного текста лабораторных исследований."""

    source_text = TextAreaField(
        "Исходный текст лабораторных исследований",
        validators=[DataRequired()],
    )

    ai_conclusion = TextAreaField(
        "Интерпретация лабораторных исследований",
        validators=[Optional()],
    )

    submit = SubmitField("Сохранить")
