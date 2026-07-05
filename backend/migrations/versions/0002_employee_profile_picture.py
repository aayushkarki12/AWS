"""Add profile_picture_url to employees

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-05
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees", sa.Column("profile_picture_url", sa.String(500), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("employees", "profile_picture_url")
