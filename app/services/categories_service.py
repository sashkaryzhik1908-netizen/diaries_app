from sqlalchemy import select

from app.extensions import db
from app.models import Category, DiaryEntry, TemplateVariable, VariableOption


def create_category(name, slug, template, order):

    category = Category(
        name=name,
        slug=slug,
        order=order,
        template=template,
    )

    db.session.add(category)
    db.session.commit()

    return category


def update_category(category, name, slug, order, template):
    category.name = name
    category.slug = slug
    category.template = template
    category.order = order

    db.session.commit()


def delete_category(category):
    existing_entries = db.session.scalar(
        select(DiaryEntry).where(DiaryEntry.category_id == category.id)
    )

    if existing_entries:
        return False

    db.session.delete(category)
    db.session.commit()

    return True


def create_variable(category_id, name, label, field_type, required, order):
    variable = TemplateVariable(
        category_id=category_id,
        name=name,
        label=label,
        field_type=field_type,
        required=required,
        order=order,
    )

    db.session.add(variable)
    db.session.commit()

    return variable


def update_variable(variable, name, label, field_type, required, order):
    variable.name = name
    variable.label = label
    variable.field_type = field_type
    variable.required = required
    variable.order = order

    db.session.commit()


def delete_variable(variable):
    db.session.delete(variable)
    db.session.commit()


def create_option(variable_id, value, output_value):
    option = VariableOption(
        variable_id=variable_id,
        value=value,
        output_value=output_value,
    )

    db.session.add(option)
    db.session.commit()

    return option


def update_option(option, value, output_value):
    option.value = value
    option.output_value = output_value

    db.session.commit()


def delete_option(option):
    db.session.delete(option)
    db.session.commit()
