from datetime import datetime
from sfrCore import Item

from lib.importers.abstractImporter import AbstractImporter
from helpers.logHelpers import createLog

logger = createLog('accessImporter')


class AccessReportImporter(AbstractImporter):
    def __init__(self, record, session, kinesisMsgs, sqsMsgs):
        self.data = record['data']
        self.item = None
        self.logger = self.createLogger()
        super().__init__(record, session)

    @property
    def identifier(self):
        return self.item.id

    def lookupRecord(self):
        self.logger.info('Ingest Accessibility Report')

        return self.insertRecord()

    def insertRecord(self):
        accessReport = Item.addReportData(self.session, self.data)

        if not accessReport:
            return 'error'

        self.item = accessReport.item
        self.session.add(accessReport)
        return 'insert'

    def setInsertTime(self):
        self.item.instance.work.date_modified = datetime.utcnow()

    def createLogger(self):
        return logger
