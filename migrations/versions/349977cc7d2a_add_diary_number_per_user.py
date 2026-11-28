"""add diary number per user

Revision ID: YOUR_REVISION_ID
Revises: 879fb146899e
"""

import sqlalchemy as sa
from alembic import op

revision = "349977cc7d2a"
down_revision = "879fb146899e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "diary",
        sa.Column("number", sa.Integer(), nullable=True),
    )

    connection = op.get_bind()

    diaries = connection.execute(
        sa.text("SELECT id, user_id FROM diary ORDER BY user_id, id")
    ).fetchall()

    numbers = {}

    for diary in diaries:
        user_id = diary.user_id

        numbers[user_id] = numbers.get(user_id, 0) + 1

        connection.execute(
            sa.text("UPDATE diary SET number = :number WHERE id = :id"),
            {
                "number": numbers[user_id],
                "id": diary.id,
            },
        )

    with op.batch_alter_table("diary") as batch_op:
        batch_op.alter_column(
            "number",
            existing_type=sa.Integer(),
            nullable=False,
        )

        batch_op.create_unique_constraint(
            "unique_user_diary_number",
            ["user_id", "number"],
        )


def downgrade():
    with op.batch_alter_table("diary") as batch_op:
        batch_op.drop_constraint(
            "unique_user_diary_number",
            type_="unique",
        )

        batch_op.drop_column("number")
