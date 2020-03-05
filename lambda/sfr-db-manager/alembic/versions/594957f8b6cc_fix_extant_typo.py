"""Fix extant typo

Revision ID: 594957f8b6cc
Revises: 1ec33478ad90
Create Date: 2019-01-09 13:25:26.301464

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '594957f8b6cc'
down_revision = '1ec33478ad90'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('instances', 'extant', new_column_name='extent')


def downgrade():
    op.alter_column('instances', 'extent', new_column_name='extant')
