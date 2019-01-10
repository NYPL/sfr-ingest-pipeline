"""Add generic identifier table

Revision ID: 06250c05785b
Revises: 87c0e214bba1
Create Date: 2019-01-08 12:26:19.054744

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06250c05785b'
down_revision = '87c0e214bba1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'generic',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('value', sa.Unicode, nullable=False, index=True),
        sa.Column('identifier_id', sa.Integer, sa.ForeignKey('identifiers.id'))
    )


def downgrade():
    op.drop_table('generic')
