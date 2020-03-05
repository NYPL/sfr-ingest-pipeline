"""Add license field to rights

Revision ID: 844b6f4ed646
Revises: 59c8cd1935d7
Create Date: 2019-02-04 14:52:40.610752

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '844b6f4ed646'
down_revision = '59c8cd1935d7'
branch_labels = None
depends_on = None


def upgrade():
     op.add_column('rights',
        sa.Column('license', sa.Unicode, nullable=True)
    )


def downgrade():
    op.drop_column('rights', 'license')
