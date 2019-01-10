"""Increase length of URL field in links table

Revision ID: d4b6e9caf603
Revises: d8506b1d5654
Create Date: 2019-01-08 13:54:35.393325

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4b6e9caf603'
down_revision = 'd8506b1d5654'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('links', 'url', type_=sa.String(255))


def downgrade():
    op.alter_column('links', 'url', type_=sa.String(125))
