"""accept link urls longer than 255 characters

Revision ID: 2ccebd233d11
Revises: 844b6f4ed646
Create Date: 2019-02-11 10:26:29.610386

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2ccebd233d11'
down_revision = '844b6f4ed646'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('links', 'url', type_=sa.Unicode)


def downgrade():
    op.alter_column('links', 'url', type_=sa.String(255))
