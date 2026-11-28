"""Add laboratory source to diary

Revision ID: 1ec2522f8aff
Revises: 177d99ed6ebb
Create Date: 2026-11-20 14:49:11.835153

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1ec2522f8aff"
down_revision = "177d99ed6ebb"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("laboratory_source", schema=None) as batch_op:
        batch_op.add_column(sa.Column("diary_id", sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column("result_text", sa.Text(), nullable=False))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=False))

        batch_op.create_unique_constraint(
            "uq_laboratory_source_diary_id",
            ["diary_id"],
        )

        batch_op.create_foreign_key(
            "fk_laboratory_source_diary_id_diary",
            "diary",
            ["diary_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("laboratory_source", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_laboratory_source_diary_id_diary",
            type_="foreignkey",
        )

        batch_op.drop_constraint(
            "uq_laboratory_source_diary_id",
            type_="unique",
        )

        batch_op.drop_column("updated_at")
        batch_op.drop_column("result_text")
        batch_op.drop_column("diary_id")
