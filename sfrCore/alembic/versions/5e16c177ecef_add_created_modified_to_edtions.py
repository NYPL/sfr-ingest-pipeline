"""Add created-modified to edtions

Revision ID: 5e16c177ecef
Revises: 5c49a8cf3064
Create Date: 2019-09-09 15:39:07.773453

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e16c177ecef'
down_revision = '5c49a8cf3064'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'editions',
        sa.Column('date_created', sa.DateTime, default=datetime.now())
    )
    op.add_column(
        'editions',
        sa.Column('date_modified',
                  sa.DateTime, default=datetime.now(), onupdate=datetime.now())
    )


def downgrade():
    op.drop_column('editions', 'date_created')
    op.drop_column('editions', 'date_modified')
