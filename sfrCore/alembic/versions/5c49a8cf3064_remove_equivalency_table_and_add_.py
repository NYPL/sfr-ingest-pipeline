"""Remove equivalency table and add editions table

Revision ID: 5c49a8cf3064
Revises: ba19a561e368
Create Date: 2019-09-05 16:40:09.497036

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import DATERANGE


# revision identifiers, used by Alembic.
revision = '5c49a8cf3064'
down_revision = 'ba19a561e368'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('equivalency')

    op.create_table(
        'editions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('work_id', sa.Integer, sa.ForeignKey('works.id')),
        sa.Column('publication_place', sa.Text),
        sa.Column('publication_date', DATERANGE),
        sa.Column('edition', sa.Text),
        sa.Column('edition_statement', sa.Text),
        sa.Column('extent', sa.Text),
        sa.Column('summary', sa.Text),
        sa.Column('table_of_contents', sa.Text),
        sa.Column('volume', sa.Text)
    )

    op.add_column(
        'instances',
        sa.Column('edition_id', sa.Integer, sa.ForeignKey('editions.id'))
    )

    op.create_index('editions_work_id', 'editions', ['work_id'])
    op.create_index('instance_edition_id', 'instances', ['edition_id'])


def downgrade():
    op.create_table(
        'equivalency',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('source_id', sa.Integer, nullable=False),
        sa.Column('target_id', sa.Integer, nullable=False),
        sa.Column('type', sa.Text, nullable=False),
        sa.Column('match_data', sa.JSON)
    )

    op.drop_table('editions')

    op.drop_column('instances', 'edition_id')
