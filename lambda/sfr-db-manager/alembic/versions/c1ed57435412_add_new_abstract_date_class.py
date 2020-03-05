"""Add new abstract date class

Revision ID: c1ed57435412
Revises: f0645598beea
Create Date: 2019-01-10 11:37:45.366597

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import DATERANGE


# revision identifiers, used by Alembic.
revision = 'c1ed57435412'
down_revision = 'f0645598beea'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'dates',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('display_date', sa.Unicode, index=True),
        sa.Column('date_range', DATERANGER, index=True),
        sa.Column('date_type', sa.Unicode, index=True),
        sa.Column('date_created', sa.DateTime, default=datetime.now()),
        sa.Column('date_modified', sa.DateTime, default=datetime.now(), onupdate=datetime.now())
    )
    op.create_table(
        'work_dates',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('work_id', sa.Integer, sa.ForeignKey('works.id')),
        sa.Column('date_id', sa.Integer, sa.ForeignKey('dates.id'))
    )
    op.create_table(
        'instance_dates',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('instance_id', sa.Integer, sa.ForeignKey('instances.id')),
        sa.Column('date_id', sa.Integer, sa.ForeignKey('dates.id'))
    )
    op.create_table(
        'item_dates',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('item_id', sa.Integer, sa.ForeignKey('item.id')),
        sa.Column('date_id', sa.Integer, sa.ForeignKey('dates.id'))
    )
    op.create_table(
        'agent_dates',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('agent_id', sa.Integer, sa.ForeignKey('agents.id')),
        sa.Column('date_id', sa.Integer, sa.ForeignKey('dates.id'))
    )

    op.drop_column('agents', 'birth_date')
    op.drop_column('agents', 'death_date')

    op.drop_column('instances', 'pub_date')

    op.drop_column('works', 'issued')
    op.drop_column('works', 'published')


def downgrade():
    op.drop_table('agent_dates')
    op.drop_table('item_dates')
    op.drop_table('instance_dates')
    op.drop_table('work_dates')
    op.drop_table('dates')

    op.add_column('agents',
        sa.Column('birth_date', sa.Date)
    )
    op.add_column('agents',
        sa.Column('death_date', sa.Date)
    )

    op.add_column('instances',
        sa.Column('pub_date', sa.Date)
    )

    op.add_column('works',
        sa.Column('issued', sa.Date)
    )

    op.add_column('works',
        sa.Column('published', sa.Date)
    )
