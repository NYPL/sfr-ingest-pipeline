"""Add dates to doab identifier table

Revision ID: 43488754bd80
Revises: 97b5fc83c0f1
Create Date: 2019-02-26 11:29:34.709102

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43488754bd80'
down_revision = '97b5fc83c0f1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'doab',
        sa.Column('date_created', sa.DateTime, default=datetime.now())
    )
    op.add_column(
        'doab',
        sa.Column(
            'date_modified',
            sa.DateTime,
            default=datetime.now(),
            onupdate=datetime.now()
        )
    )


def downgrade():
    op.drop_column('doab', 'date_created')
    op.drop_column('doab', 'date_modified')