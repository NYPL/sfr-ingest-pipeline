"""add md5 to link table

Revision ID: f0645598beea
Revises:
Create Date: 2019-01-03 16:07:55.530957

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f0645598beea'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('links',
        sa.Column('md5', sa.Unicode(), nullable=True)
    )


def downgrade():
    op.drop_column('links', 'md5')
