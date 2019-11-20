from collections import defaultdict

from helpers.logHelpers import createLog

from lib.updaters.workUpdater import WorkUpdater
from lib.updaters.instanceUpdater import InstanceUpdater
from lib.updaters.itemUpdater import ItemUpdater
from lib.updaters.coverUpdater import CoverUpdater
from lib.outputManager import OutputManager

logger = createLog('db_manager')


class DBUpdater:
    # Load Updaters for specific types of records, all based on AbstractUpdater
    UPDATERS = {
        'work': WorkUpdater,
        'instance': InstanceUpdater,
        'item': ItemUpdater,
        'cover': CoverUpdater,
    }

    def __init__(self, session):
        self.session = session
        self.logger = logger
        self.kinesisMsgs = defaultdict(list)
        self.sqsMsgs = defaultdict(list)

    def importRecord(self, record):
        recordType = record.get('type', 'work')
        logger.info('Updating {} record'.format(recordType))

        updater = self.UPDATERS[recordType](
            record, self.session, self.kinesisMsgs, self.sqsMsgs
        )
        updater.lookupRecord()
        updater.updateRecord()
        updater.setUpdateTime()

        self.logger.info('Updated {} #{}'.format(
            recordType.upper(), updater.identifier
        ))
        return '{} #{}'.format(recordType.upper(), updater.identifier)

    def sendMessages(self):
        for records, stream in self.kinesisMsgs.items():
            OutputManager.putKinesisBatch(stream, records)

        for messages, queue in self.sqsMsgs.items():
            OutputManager.putQueueBatches(queue, messages)
