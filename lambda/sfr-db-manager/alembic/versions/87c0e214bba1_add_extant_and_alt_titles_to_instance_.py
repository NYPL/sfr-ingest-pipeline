"""Add extant and alt_titles to instance table

Revision ID: 87c0e214bba1
Revises: f0645598beea
Create Date: 2019-01-08 10:26:57.927739

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '87c0e214bba1'
down_revision = 'f0645598beea'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('instances',
        sa.Column('extant', sa.Unicode(), nullable=True)
    )
    op.drop_column('instances', 'alt_title')
    op.drop_column('alt_titles', 'work_id')

    op.create_table(
        'work_alt_titles',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('work_id', sa.Integer, sa.ForeignKey('works.id')),
        sa.Column('title_id', sa.Integer, sa.ForeignKey('alt_titles.id'))
    )

    op.create_table(
        'instance_alt_titles',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('instance_id', sa.Integer, sa.ForeignKey('instances.id')),
        sa.Column('title_id', sa.Integer, sa.ForeignKey('alt_titles.id'))
    )


def downgrade():
    op.drop_column('instances', 'extant')
    op.add_column('instances',
        sa.Column('alt_title', sa.Unicode(), nullable=True)
    )
    op.add_column('alt_titles',
        sa.Column('work_id', sa.Integer, sa.ForeignKey('works.id'))
    )

    op.drop_table('work_alt_titles')
    op.drop_table('instance_alt_titles')
