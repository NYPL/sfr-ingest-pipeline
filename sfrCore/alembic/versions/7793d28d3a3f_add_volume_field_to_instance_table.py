"""Add volume field to instance table

Revision ID: 7793d28d3a3f
Revises: 43488754bd80
Create Date: 2019-03-11 09:55:47.598260

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7793d28d3a3f'
down_revision = '43488754bd80'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('instances', sa.Column('volume', sa.Unicode))


def downgrade():
    op.drop_column('instances', 'volume')
