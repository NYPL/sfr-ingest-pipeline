"""Create record equivalency table

Revision ID: 598c2b4a46e3
Revises: 47961539f636
Create Date: 2019-03-18 10:17:57.678558

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '598c2b4a46e3'
down_revision = '7793d28d3a3f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('equivalents',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('source_id', sa.Integer, nullable=False, index=True),
        sa.Column('target_id', sa.Integer, nullable=False, index=True),
        sa.Column('type', sa.Unicode, index=True),
        sa.Column('match_data', sa.JSON)
    )


def downgrade():
    op.delete_table('equivalents')
