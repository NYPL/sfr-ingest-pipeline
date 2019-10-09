from helpers.logHelpers import createLog

from lib.updaters.workUpdater import WorkUpdater
from lib.updaters.instanceUpdater import InstanceUpdater
from lib.updaters.itemUpdater import ItemUpdater
from lib.updaters.coverUpdater import CoverUpdater

logger = createLog('db_manager')

# Load Updaters for specific types of records, all based on AbstractUpdater
updaters = {
    'work': WorkUpdater,
    'instance': InstanceUpdater,
    'item': ItemUpdater,
    'cover': CoverUpdater,
}


def importRecord(session, record):
    recordType = record.get('type', 'work')
    logger.info('Updating {} record'.format(recordType))

    updater = updaters[recordType](record, session)  # Create specific updater
    updater.lookupRecord()
    updater.updateRecord()
    updater.setUpdateTime()

    logger.info('Updated {} #{}'.format(
        recordType.upper(), updater.identifier
    ))
    return '{} #{}'.format(recordType.upper(), updater.identifier)
