from lib.importers.workImporter import WorkImporter
from lib.importers.instanceImporter import InstanceImporter
from lib.importers.itemImporter import ItemImporter
from lib.importers.accessImporter import AccessReportImporter
from lib.importers.coverImporter import CoverImporter

from helpers.logHelpers import createLog

logger = createLog('db_manager')

# Load Updaters for specific types of records, all based on AbstractUpdater
importers = {
    'work': WorkImporter,
    'instance': InstanceImporter,
    'item': ItemImporter,
    'access_report': AccessReportImporter,
    'cover': CoverImporter
}


def importRecord(session, record):
    recordType = record.get('type', 'work')
    logger.info('Updating {} record'.format(recordType))

    # Create specific importer
    importer = importers[recordType](record, session)
    action = importer.lookupRecord()
    if action == 'insert':
        importer.setInsertTime()

    logger.info('{} {} #{}'.format(
        action, recordType.upper(), importer.identifier
    ))
    return '{} {} #{}'.format(action, recordType.upper(), importer.identifier)
