"""add diary owner

Revision ID: 879fb146899e
Revises: 45f9faef7efe
Create Date: 2026-11-16 19:35:27.564426

"""

import sqlalchemy as sa
from alembic import op

revision = "879fb146899e"
down_revision = "45f9faef7efe"
branch_labels = None
depends_on = None


def upgrade():
    # Удаляем старые дневники
    op.execute("DELETE FROM diary_entry")
    op.execute("DELETE FROM therapy_group")
    op.execute("DELETE FROM diary")

    # Добавляем владельца дневника
    with op.batch_alter_table("diary") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=False))
        batch_op.create_foreign_key(
            "fk_diary_user_id_user",
            "user",
            ["user_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("diary") as batch_op:
        batch_op.drop_constraint(
            "fk_diary_user_id_user",
            type_="foreignkey",
        )
        batch_op.drop_column("user_id")
