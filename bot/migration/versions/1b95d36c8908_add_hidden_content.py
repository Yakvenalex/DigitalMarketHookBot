"""add hidden content

Revision ID: 1b95d36c8908
Revises: 2fda6446e69f
Create Date: 2024-12-20 14:47:07.064138

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b95d36c8908'
down_revision: Union[str, None] = '2fda6446e69f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('hidden_content', sa.Text(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('products', 'hidden_content')
    # ### end Alembic commands ###
