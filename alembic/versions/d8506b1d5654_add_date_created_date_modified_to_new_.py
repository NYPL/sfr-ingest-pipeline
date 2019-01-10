"""Add date_created, date_modified to new tables

Revision ID: d8506b1d5654
Revises: 06250c05785b
Create Date: 2019-01-08 13:46:07.108377

"""
from datetime import datetime
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8506b1d5654'
down_revision = '06250c05785b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('generic',
        sa.Column(
            'date_created',
            sa.DateTime,
            default=datetime.now(),
            onupdate=datetime.now()
        )
    )

    op.add_column('generic',
        sa.Column(
            'date_modified',
            sa.DateTime,
            default=datetime.now(),
            onupdate=datetime.now()
        )
    )

    op.add_column('work_alt_titles',
        sa.Column(
            'date_created',
            sa.DateTime,
            default=datetime.now(),
            onupdate=datetime.now()
        )
    )

    op.add_column('work_alt_titles',
        sa.Column(
            'date_modified',
            sa.DateTime,
            default=datetime.now(),
            onupdate=datetime.now()
        )
    )

    op.add_column('instance_alt_titles',
        sa.Column(
            'date_created',
            sa.DateTime,
            default=datetime.now(),
            onupdate=datetime.now()
        )
    )

    op.add_column('instance_alt_titles',
        sa.Column(
            'date_modified',
            sa.DateTime,
            default=datetime.now(),
            onupdate=datetime.now()
        )
    )


def downgrade():
    op.drop_column('generic', 'date_created')
    op.drop_column('generic', 'date_modified')
    op.drop_column('work_alt_titles', 'date_created')
    op.drop_column('work_alt_titles', 'date_modified')
    op.drop_column('instance_alt_titles', 'date_created')
    op.drop_column('instance_alt_titles', 'date_modified')
