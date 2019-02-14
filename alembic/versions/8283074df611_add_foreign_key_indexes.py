"""Add foreign key indexes

Revision ID: 8283074df611
Revises: 58b5c31ba2e3
Create Date: 2019-02-14 11:56:05.649112

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8283074df611'
down_revision = '58b5c31ba2e3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('instance_works', 'instances', ['work_id'])
    op.create_index('item_instances', 'items', ['instance_id'])

    op.create_index('work_json', 'import_json', ['work_id'])


    op.create_index('agent_alias', 'aliases', ['agent_id'])
    
    op.create_index('work_agents_work', 'agent_works', ['work_id'])
    op.create_index('work_agents_agent', 'agent_works', ['agent_id'])
    op.create_index('instance_agents_instance', 'agent_instances', ['instance_id'])
    op.create_index('instance_agents_agent', 'agent_instances', ['agent_id'])
    op.create_index('item_agents_item', 'agent_items', ['item_id'])
    op.create_index('item_agents_agent', 'agent_items', ['agent_id'])
    
    op.create_index('work_identifiers_work', 'work_identifiers', ['work_id'])
    op.create_index('work_identifiers_identifier', 'work_identifiers', ['identifier_id'])
    op.create_index('instance_identifiers_instance', 'instance_identifiers', ['instance_id'])
    op.create_index('instance_identifiers_identifier', 'instance_identifiers', ['identifier_id'])
    op.create_index('item_identifiers_item', 'item_identifiers', ['item_id'])
    op.create_index('item_identifiers_identifier', 'item_identifiers', ['identifier_id'])

    op.create_index('hathi_id', 'hathi', ['identifier_id'])
    op.create_index('gutenberg_id', 'gutenberg', ['identifier_id'])
    op.create_index('lccn_id', 'lccn', ['identifier_id'])
    op.create_index('lcc_id', 'lcc', ['identifier_id'])
    op.create_index('ddc_id', 'ddc', ['identifier_id'])
    op.create_index('isbn_id', 'hathi', ['identifier_id'])
    op.create_index('issn_id', 'issn', ['identifier_id'])
    op.create_index('oclc_id', 'oclc', ['identifier_id'])
    op.create_index('owi_id', 'owi', ['identifier_id'])
    op.create_index('generic_id', 'generic', ['identifier_id'])

    op.create_index('work_subjects_subject', 'subject_works', ['subject_id'])
    op.create_index('work_subjects_work', 'subject_works', ['work_id'])

    op.create_index('work_dates_work', 'work_dates', ['work_id'])
    op.create_index('work_dates_date', 'work_dates', ['date_id'])
    op.create_index('instance_dates_instance', 'instance_dates', ['instance_id'])
    op.create_index('instance_dates_date', 'instance_dates', ['date_id'])
    op.create_index('item_dates_item', 'item_dates', ['item_id'])
    op.create_index('item_dates_date', 'item_dates', ['date_id'])
    op.create_index('agent_dates_agent', 'agent_dates', ['agent_id'])
    op.create_index('agent_dates_date', 'agent_dates', ['date_id'])

    op.create_index('work_measurements_work', 'work_measurements', ['work_id'])
    op.create_index('work_measurements_measurement', 'work_measurements', ['measurement_id'])
    op.create_index('instance_measurements_instance', 'instance_measurements', ['instance_id'])
    op.create_index('instance_measurements_measurement', 'instance_measurements', ['measurement_id'])
    op.create_index('item_measurements_item', 'item_measurements', ['item_id'])
    op.create_index('item_measurements_measurement', 'item_measurements', ['measurement_id'])
    
    op.create_index('work_rights_work', 'work_rights', ['work_id'])
    op.create_index('work_rights_rights', 'work_rights', ['rights_id'])
    op.create_index('instance_rights_instance', 'instance_rights', ['instance_id'])
    op.create_index('instance_rights_rights', 'instance_rights', ['rights_id'])
    op.create_index('item_rights_item', 'item_rights', ['item_id'])
    op.create_index('item_rights_rights', 'item_rights', ['rights_id'])

    op.create_index('work_links_work', 'work_links', ['work_id'])
    op.create_index('work_links_link', 'work_links', ['link_id'])
    op.create_index('instance_links_instance', 'instance_links', ['instance_id'])
    op.create_index('instance_links_link', 'instance_links', ['link_id'])
    op.create_index('item_links_item', 'item_links', ['item_id'])
    op.create_index('item_links_link', 'item_links', ['link_id'])

    op.create_index('work_alt_titles_work', 'work_alt_titles', ['work_id'])
    op.create_index('work_alt_titles_alt_title', 'work_alt_titles', ['title_id'])
    op.create_index('instance_alt_titles_instance', 'instance_alt_titles', ['instance_id'])
    op.create_index('instance_alt_titles_alt_title', 'instance_alt_titles', ['title_id'])

    

def downgrade():
    op.drop_index('instance_works')
    op.drop_index('item_instances')

    op.drop_index('work_json')


    op.drop_index('agent_alias')
    
    op.drop_index('work_agents_work')
    op.drop_index('work_agents_agent')
    op.drop_index('instance_agents_instance')
    op.drop_index('instance_agents_agent')
    op.drop_index('item_agents_item')
    op.drop_index('item_agents_agent')
    
    op.drop_index('work_identifiers_work')
    op.drop_index('work_identifiers_identifier')
    op.drop_index('instance_identifiers_instance')
    op.drop_index('instance_identifiers_identifier')
    op.drop_index('item_identifiers_item')
    op.drop_index('item_identifiers_identifier')

    op.drop_index('hathi_id')
    op.drop_index('gutenberg_id')
    op.drop_index('lccn_id')
    op.drop_index('lcc_id')
    op.drop_index('ddc_id')
    op.drop_index('isbn_id')
    op.drop_index('issn_id')
    op.drop_index('oclc_id')
    op.drop_index('owi_id')
    op.drop_index('generic_id')

    op.drop_index('work_subjects_subject')
    op.drop_index('work_subjects_work')

    op.drop_index('work_dates_work')
    op.drop_index('work_dates_date')
    op.drop_index('instance_dates_instance')
    op.drop_index('instance_dates_date')
    op.drop_index('item_dates_item')
    op.drop_index('item_dates_date')
    op.drop_index('agent_dates_agent')
    op.drop_index('agent_dates_date')

    op.drop_index('work_measurements_work')
    op.drop_index('work_measurements_measurement')
    op.drop_index('instance_measurements_instance')
    op.drop_index('instance_measurements_measurement')
    op.drop_index('item_measurements_item')
    op.drop_index('item_measurements_measurement')
    
    op.drop_index('work_rights_work')
    op.drop_index('work_rights_rights')
    op.drop_index('instance_rights_instance')
    op.drop_index('instance_rights_rights')
    op.drop_index('item_rights_item')
    op.drop_index('item_rights_rights')

    op.drop_index('work_links_work')
    op.drop_index('work_links_link')
    op.drop_index('instance_links_instance')
    op.drop_index('instance_links_link')
    op.drop_index('item_links_item')
    op.drop_index('item_links_link')

    op.drop_index('work_alt_titles_work')
    op.drop_index('work_alt_titles_alt_title')
    op.drop_index('instance_alt_titles_instance')
    op.drop_index('instance_alt_titles_alt_title')
