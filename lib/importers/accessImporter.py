from datetime import datetime
from sfrCore import Item

from lib.importers.abstractImporter import AbstractImporter


class AccessReportImporter(AbstractImporter):
    def __init__(self, record, session):
        self.data = record['data']
        self.item = None
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
        return 'insert'

    def setInsertTime(self):
        self.item.instance.work.date_modified = datetime.utcnow()
