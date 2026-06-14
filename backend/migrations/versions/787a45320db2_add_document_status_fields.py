"""add document status fields

Revision ID: 787a45320db2
Revises: 
Create Date: 2026-06-14 00:31:08.580601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '787a45320db2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("processed_at", sa.DateTime(), nullable=True))
    op.add_column("documents", sa.Column("error_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "processed_at")
    op.drop_column("documents", "error_message")