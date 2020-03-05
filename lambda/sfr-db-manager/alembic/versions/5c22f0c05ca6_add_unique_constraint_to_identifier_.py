"""Add unique constraint to identifier tables

Revision ID: 5c22f0c05ca6
Revises: 7793d28d3a3f
Create Date: 2019-03-18 14:48:31.640919

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c22f0c05ca6'
down_revision = '7793d28d3a3f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint('uq_value_doab', 'doab', 'value')
    op.create_unique_constraint('uq_value_hathi', 'hathi', 'value')
    op.create_unique_constraint('uq_value_gutenberg', 'gutenberg', 'value')
    op.create_unique_constraint('uq_value_oclc', 'oclc', 'value')
    op.create_unique_constraint('uq_value_lccn', 'lccn', 'value')
    op.create_unique_constraint('uq_value_owi', 'owi', 'value')
    op.create_unique_constraint('uq_value_issn', 'issn', 'value')
    op.create_unique_constraint('uq_value_ddc', 'ddc', 'value')
    op.create_unique_constraint('uq_value_generic', 'generic', 'value')


def downgrade():
    op.drop_constraint('uq_value_doab', 'doab')
    op.drop_constraint('uq_value_hathi', 'hathi')
    op.drop_constraint('uq_value_gutenberg', 'gutenberg')
    op.drop_constraint('uq_value_oclc', 'oclc')
    op.drop_constraint('uq_value_lccn', 'lccn')
    op.drop_constraint('uq_value_owi', 'owi')
    op.drop_constraint('uq_value_issn', 'issn')
    op.drop_constraint('uq_value_ddc', 'ddc')
    op.drop_constraint('uq_value_generic', 'generic')
