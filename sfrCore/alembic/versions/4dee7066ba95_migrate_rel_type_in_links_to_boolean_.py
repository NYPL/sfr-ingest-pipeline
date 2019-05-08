"""Migrate rel_type in links to boolean logic

Revision ID: 4dee7066ba95
Revises: cf57270f4c4e
Create Date: 2019-05-07 11:52:07.558823

"""
from alembic import op
import sqlalchemy as sa

import json


# revision identifiers, used by Alembic.
revision = '4dee7066ba95'
down_revision = 'cf57270f4c4e'
branch_labels = None
depends_on = None

linkHelper = sa.Table(
    'links',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('rel_type', sa.String(length=50)),
    sa.Column('media_type', sa.String(length=50)),
    sa.Column('flags', sa.dialects.postgresql.JSON(), nullable=True)
)

typeTranslation = {
    'associated': {'local': False, 'download': False, 'ebook': False},
    'archive': {'local': True, 'download': True, 'images': True, 'ebook': True},
    'ebook': {'local': False, 'download': True, 'images': True, 'ebook': True},
    'pdf_download': {'local': False, 'download': True, 'images': True, 'ebook': True},
    'explMain': {'local': True, 'download': False, 'images': True, 'ebook': True},
    'description': {'local': False, 'download': False, 'ebook': False},
    'external_view': {'local': False, 'download': False, 'images': True, 'ebook': True},
    None: {'local': False, 'download': False, 'ebook': False}
}

def upgrade():
    conn = op.get_bind()

    op.add_column(
        'links',
        sa.Column('flags', sa.dialects.postgresql.JSON(), nullable=True)
    )

    for link in conn.execute(linkHelper.select()):
        flagJSON = json.dumps(typeTranslation[link.rel_type])
        print(link.rel_type, flagJSON)
        conn.execute(
            linkHelper.update().where(linkHelper.c.id == link.id).values(flags=flagJSON)
        )

    op.drop_column('links', 'rel_type')

def downgrade():
    
    conn = op.get_bind()
    op.add_column('rel_type', sa.String(length=50))

    for link in conn.execute(linkHelper.select()):
        flags = json.loads(link.flags)
        relType = 'description'
        if flags['local'] and flags['download'] and flags['ebook']:
            relType = 'archive'
        elif flags['local'] and flags['ebook']:
            relType = 'explMain'
        elif flags['download'] and flags['ebook'] and link.media_type == 'application/pdf':
            relType = 'pdf_download'
        elif flags['download'] and flags['ebook']:
            relType = 'ebook'
        elif flags['ebook']:
            relType = 'external_view'
        linkHelper.update().where(linkHelper.c.id == link.id).values(rel_type=relType)
    
    op.drop_column('links', 'flags')
