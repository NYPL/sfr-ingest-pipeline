from collections import defaultdict

from lib.importers.workImporter import WorkImporter
from lib.importers.instanceImporter import InstanceImporter
from lib.importers.itemImporter import ItemImporter
from lib.importers.accessImporter import AccessReportImporter
from lib.importers.coverImporter import CoverImporter
from lib.outputManager import OutputManager

from helpers.logHelpers import createLog

logger = createLog('db_manager')


class DBManager:
    # Load Updaters for specific types of records, all based on AbstractUpdater
    IMPORTERS = {
        'work': WorkImporter,
        'instance': InstanceImporter,
        'item': ItemImporter,
        'access_report': AccessReportImporter,
        'cover': CoverImporter
    }

    def __init__(self, session):
        self.session = session
        self.logger = logger
        self.kinesisMsgs = defaultdict(list)
        self.sqsMsgs = defaultdict(list)

    def importRecord(self, record):
        recordType = record.get('type', 'work')
        logger.info('Updating {} record'.format(recordType))

        # Create specific importer
        importer = self.IMPORTERS[recordType](
            record, self.session, self.kinesisMsgs, self.sqsMsgs
        )
        action = importer.lookupRecord()
        if action == 'insert':
            importer.setInsertTime()

        self.logger.info('{} {} #{}'.format(
            action, recordType.upper(), importer.identifier
        ))
        return '{} {} #{}'.format(
            action, recordType.upper(), importer.identifier
        )

    def sendMessages(self):
        for stream, records in self.kinesisMsgs.items():
            OutputManager.putKinesisBatch(stream, records)

        for queue, messages in self.sqsMsgs.items():
            OutputManager.putQueueBatches(queue, messages)
