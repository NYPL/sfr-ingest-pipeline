"""DOAB Model Revisions (Language, Identifier & Work Summary)

Revision ID: 97b5fc83c0f1
Revises: 8283074df611
Create Date: 2019-02-22 10:51:09.578807

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '97b5fc83c0f1'
down_revision = '8283074df611'
branch_labels = None
depends_on = None


def upgrade():
    # Insert new language table, relational table and drop existing
    # language fields
    op.create_table(
        'language',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('language', sa.Unicode, index=True),
        sa.Column('iso_2', sa.String(2), index=True, unique=True),
        sa.Column('iso_3', sa.String(3), index=True),
        sa.Column('date_created', sa.DateTime, default=datetime.now()),
        sa.Column(
            'date_modified',
            sa.DateTime,
            default=datetime.now(),
            onupdate=datetime.now()
        )
    )
    op.create_table(
        'work_language',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('work_id', sa.Integer, sa.ForeignKey('works.id'), index=True),
        sa.Column('language_id', sa.Integer, sa.ForeignKey('language.id'), index=True)
    )
    op.create_table(
        'instance_language',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('instance_id', sa.Integer, sa.ForeignKey('instances.id'), index=True),
        sa.Column('language_id', sa.Integer, sa.ForeignKey('language.id'), index=True)
    )

    op.drop_column('works', 'language')
    op.drop_column('instances', 'language')

    # Add identifier table for DOAB identifiers
    op.create_table(
        'doab',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('value', sa.Unicode, nullable=False, index=True),
        sa.Column('identifier_id', sa.Integer, sa.ForeignKey('identifiers.id'), index=True)
    )

    # Add column for full-text work summaries
    op.add_column('works', sa.Column('summary', sa.Unicode))


def downgrade():
    op.drop_table('work_language')
    op.drop_table('instance_language')
    op.drop_table('language')
    

    op.add_column('works', sa.Column('language', sa.String(2)))
    op.add_column('instances', sa.Column('language', sa.String(2)))

    op.drop_table('doab')

    op.drop_column('works', 'summary')
