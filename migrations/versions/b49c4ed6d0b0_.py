"""empty message

Revision ID: b49c4ed6d0b0
Revises: 
Create Date: 2025-02-04 15:26:03.123721

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b49c4ed6d0b0'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('recipes', 'ingredients',
               existing_type=sa.VARCHAR(length=255),
               type_=postgresql.JSONB(astext_type=sa.Text()),
               existing_nullable=False,
               postgresql_using="ingredients::jsonb")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('recipes', 'ingredients',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False)
    # ### end Alembic commands ###
