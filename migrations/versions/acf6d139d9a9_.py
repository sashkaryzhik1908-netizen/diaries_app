"""empty message

Revision ID: acf6d139d9a9
Revises: 6cf276abfd61
Create Date: 2026-11-23 21:22:45.403073
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "acf6d139d9a9"
down_revision = "6cf276abfd61"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "instrumental_alias",
        "study_id",
        new_column_name="indicator_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )


def downgrade():
    op.alter_column(
        "instrumental_alias",
        "indicator_id",
        new_column_name="study_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
