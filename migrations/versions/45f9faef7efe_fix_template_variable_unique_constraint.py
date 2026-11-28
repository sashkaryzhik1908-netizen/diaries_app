"""fix template variable unique constraint

Revision ID: 45f9faef7efe
Revises: 7a3e5f609978
Create Date: 2026-11-16 19:16:54.559099

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "45f9faef7efe"
down_revision = "7a3e5f609978"
branch_labels = None
depends_on = None


def upgrade():
    naming_convention = {"uq": "uq_%(table_name)s_%(column_0_name)s"}

    with op.batch_alter_table(
        "template_variable",
        naming_convention=naming_convention,
    ) as batch_op:
        batch_op.drop_constraint(
            op.f("uq_template_variable_name"),
            type_="unique",
        )


def downgrade():
    naming_convention = {"uq": "uq_%(table_name)s_%(column_0_name)s"}

    with op.batch_alter_table(
        "template_variable",
        naming_convention=naming_convention,
    ) as batch_op:
        batch_op.create_unique_constraint(
            op.f("uq_template_variable_name"),
            ["name"],
        )
