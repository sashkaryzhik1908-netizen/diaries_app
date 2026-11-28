from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class InstrumentalIndicatorForm(FlaskForm):
    """Форма инструментальных методов исследований."""

    name = StringField(
        "Название исследования",
        validators=[
            DataRequired(),
            Length(max=150),
        ],
    )
    submit = SubmitField("Сохранить")


class InstrumentalAliasForm(FlaskForm):
    """Форма альтернативного названия инструментального исследования."""

    indicator_id = SelectField(
        "Метод исследования",
        coerce=int,
        validators=[DataRequired()],
    )
    alias = StringField(
        "Альтернативное название",
        validators=[
            DataRequired(),
            Length(max=200),
        ],
    )
    submit = SubmitField("Сохранить")


class InstrumentalSourceForm(FlaskForm):
    """Форма исходного текста инструментальных исследований."""

    source_text = TextAreaField(
        "Исходный текст инструментальных исследований",
        validators=[DataRequired()],
    )
    submit = SubmitField("Сохранить")
