"""Add HathiTrust identifiers table

Revision ID: 92889e3da8fd
Revises: 844b6f4ed646
Create Date: 2019-02-05 09:59:55.166085

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92889e3da8fd'
down_revision = '844b6f4ed646'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'hathi',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('value', sa.Unicode, nullable=False, index=True),
        sa.Column('identifier_id', sa.Integer, sa.ForeignKey('identifiers.id'))
    )


def downgrade():
    op.drop_table('hathi')
