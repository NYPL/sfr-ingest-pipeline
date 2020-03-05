"""Add license and rights_statement fields to instances

Revision ID: 1ec33478ad90
Revises: d4b6e9caf603
Create Date: 2019-01-08 18:37:24.100668

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ec33478ad90'
down_revision = 'd4b6e9caf603'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('instances',
        sa.Column('license', sa.String(255), nullable=True)
    )
    op.add_column('instances',
        sa.Column('rights_statement', sa.Unicode, nullable=True)
    )


def downgrade():
    op.drop_column('instances', 'license')
    op.drop_column('instances', 'rights_statement')
