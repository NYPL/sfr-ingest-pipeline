"""Add source_id to measurements

Revision ID: e3ba880f3706
Revises: 5c22f0c05ca6
Create Date: 2019-03-18 17:08:34.417343

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3ba880f3706'
down_revision = '5c22f0c05ca6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('measurements',
        sa.Column('source_id', sa.Unicode, index=True)
    )


def downgrade():
    op.drop_column('measurements', 'source_id')
