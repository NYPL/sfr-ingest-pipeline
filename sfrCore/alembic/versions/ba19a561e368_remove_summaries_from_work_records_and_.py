"""Remove summaries from Work records and place on instances

Revision ID: ba19a561e368
Revises: 4dee7066ba95
Create Date: 2019-08-01 15:40:16.999177

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba19a561e368'
down_revision = '4dee7066ba95'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('works', 'summary')
    op.add_column(
        'instances',
        sa.Column('summary', sa.Unicode)
    )


def downgrade():
    op.drop_column('instances', 'summary')
    op.add_column(
        'works',
        sa.Column('summary', sa.Unicode)
    )
