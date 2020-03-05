"""Add new abstract rights class

Revision ID: 59c8cd1935d7
Revises: d7f930355ed1
Create Date: 2019-02-01 16:29:34.441348

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '59c8cd1935d7'
down_revision = 'd7f930355ed1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'rights',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('source', sa.Unicode, index=True),
        sa.Column('rights_statement', sa.Unicode, index=True),
        sa.Column('rights_reason', sa.Unicode, index=True),
        sa.Column('date_created', sa.DateTime, default=datetime.now()),
        sa.Column(
            'date_modified',
            sa.DateTime,
            default=datetime.now(),
            onupdate=datetime.now()
        )
    )
    op.create_table(
        'work_rights',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('work_id', sa.Integer, sa.ForeignKey('works.id')),
        sa.Column('rights_id', sa.Integer, sa.ForeignKey('rights.id'))
    )
    op.create_table(
        'instance_rights',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('instance_id', sa.Integer, sa.ForeignKey('instances.id')),
        sa.Column('rights_id', sa.Integer, sa.ForeignKey('rights.id'))
    )
    op.create_table(
        'item_rights',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('item_id', sa.Integer, sa.ForeignKey('items.id')),
        sa.Column('rights_id', sa.Integer, sa.ForeignKey('rights.id'))
    )
    op.create_table(
        'rights_dates',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('rights_id', sa.Integer, sa.ForeignKey('rights.id')),
        sa.Column('date_id', sa.Integer, sa.ForeignKey('dates.id'))
    )

    op.drop_column('works', 'license')
    op.drop_column('works', 'rights_statement')

    op.drop_column('instances', 'license')
    op.drop_column('instances', 'rights_statement')

    op.drop_column('items', 'rights_uri')

def downgrade():
    op.drop_table('rights_dates')
    op.drop_table('item_rights')
    op.drop_table('instance_rights')
    op.drop_table('work_rights')
    op.drop_table('rights')

    op.add_column('works',
        sa.Column('license', sa.Unicode)
    )
    op.add_column('works',
        sa.Column('rights_statement', sa.Unicode)
    )

    op.add_column('instance',
        sa.Column('license', sa.Unicode)
    )
    op.add_column('instance',
        sa.Column('rights_statement', sa.Unicode)
    )

    op.add_column('item',
        sa.Column('rights_uri', sa.Unicode)
    )


