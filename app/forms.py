from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.fields.choices import SelectChoice
from wtforms.validators import (
    DataRequired,
    EqualTo,
    Length,
    Optional,
    ValidationError,
)


# Формы
class RegisterForm(FlaskForm):
    username = StringField(
        "Имя пользователя",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    name = StringField(
        "ФИО отображаемое при заполнении дневника",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(),
            EqualTo("confirm", message="Пароли должны совпадать"),
        ],
    )
    confirm = PasswordField(
        "Подтвердите пароль",
        validators=[DataRequired()],
    )
    submit = SubmitField("Зарегистрироваться")


class EditUserForm(FlaskForm):
    username = StringField(
        "Имя пользователя",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    name = StringField(
        "ФИО отображаемое при заполнении дневника",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    password = PasswordField(
        "Новый пароль",
        validators=[
            Optional(),
            EqualTo("confirm", message="Пароли должны совпадать"),
        ],
        render_kw={"autocomplete": "new-password"},
    )

    confirm = PasswordField(
        "Подтвердите новый пароль",
        validators=[Optional()],
        render_kw={"autocomplete": "new-password"},
    )
    submit = SubmitField("Сохранить")

    def validate_confirm(self, field):
        if self.password.data and not field.data:
            raise ValidationError("Подтвердите новый пароль.")

        if field.data and not self.password.data:
            raise ValidationError("Введите новый пароль.")


class LoginForm(FlaskForm):
    username = StringField(
        "Имя пользователя",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    password = PasswordField(
        "Пароль",
        validators=[DataRequired()],
    )
    submit = SubmitField("Войти")


class CategoryForm(FlaskForm):
    name = StringField(
        "Введите название категории",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    slug = StringField(
        "Введите техническое название категории",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    template = TextAreaField(
        "Шаблон категории",
        validators=[DataRequired()],
    )
    order = IntegerField("Порядок расположения категории", validators=[DataRequired()])
    submit = SubmitField("Сохранить изменения")


class TemplateVariableForm(FlaskForm):
    name = StringField(
        "Техническое имя",
        validators=[
            DataRequired(),
            Length(max=100),
        ],
    )
    label = StringField(
        "Название поля",
        validators=[
            DataRequired(),
            Length(max=150),
        ],
    )
    field_type = SelectField(
        "Тип поля",
        choices=[
            SelectChoice("select", "Один вариант"),
            SelectChoice("multiselect", "Несколько вариантов"),
            SelectChoice("text", "Текст"),
            SelectChoice("number", "Число"),
            SelectChoice("date", "Дата"),
        ],
        validators=[DataRequired()],
    )
    required = BooleanField("Обязательное поле")
    order = IntegerField(
        "Порядок расположения при заполнении дневника", validators=[DataRequired()]
    )
    submit = SubmitField("Сохранить")


class VariableOptionForm(FlaskForm):
    value = StringField(
        "Значение",
        validators=[
            DataRequired(),
            Length(max=255),
        ],
    )
    output_value = StringField(
        "Выводимое значение",
        validators=[
            DataRequired(),
            Length(max=255),
        ],
    )

    submit = SubmitField("Сохранить")


class TherapyPurposeForm(FlaskForm):
    name = StringField(
        "Название цели терапии",
        validators=[
            DataRequired(),
            Length(max=150),
        ],
    )
    output_value = StringField(
        "Отображаемое значение",
        validators=[
            DataRequired(),
            Length(max=200),
        ],
    )
    submit = SubmitField("Сохранить")


class TherapyMedicationForm(FlaskForm):
    name = StringField(
        "Название препарата",
        validators=[
            DataRequired(),
            Length(max=200),
        ],
    )
    purpose = SelectMultipleField(
        "Цель",
        choices=[],
    )
    submit = SubmitField("Сохранить")


class TherapySourceForm(FlaskForm):
    name = StringField(
        "Название группы дополнительных параметров терапии",
        validators=[
            DataRequired(),
            Length(max=200),
        ],
    )
    submit = SubmitField("Сохранить")


class TherapySourceValueForm(FlaskForm):
    name = StringField(
        "Название значения дополнительного параметра терапии",
        validators=[
            DataRequired(),
            Length(max=200),
        ],
    )
    source = SelectField(
        "Группа дополнительного параметра терапии",
        choices=[],
    )
    submit = SubmitField("Сохранить")
