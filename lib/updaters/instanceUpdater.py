from datetime import datetime
import os

from .abstractUpdater import AbstractUpdater
from sfrCore import Instance
from helpers.errorHelpers import DBError
from helpers.logHelpers import createLog

logger = createLog('instanceUpdater')


class InstanceUpdater(AbstractUpdater):
    def __init__(self, record, session, kinesisMsgs, sqsMsgs):
        self.data = record.get('data')
        self.attempts = int(record.get('attempts', 0))
        self.instance = None
        self.logger = self.createLogger()
        super().__init__(record, session, kinesisMsgs, sqsMsgs)

    @property
    def identifier(self):
        return self.instance.id

    def lookupRecord(self):
        existingID = Instance.lookup(
            self.session,
            self.data.get('identifiers', []),
            self.data.get('volume', None),
            self.data.pop('primary_identifier', None)
        )
        if existingID is None:
            if self.attempts < 3:
                self.logger.warning(
                    'Attempt {} Could not locate instance,\
                     placing at end of queue'.format(
                        self.attempts + 1
                    )
                )
                self.kinesisMsgs[os.environ['UPDATE_STREAM']].append({
                    'data': self.data,
                    'recType': 'instance',
                    'attempts': self.attempts + 1
                })
                raise DBError(
                    'instances',
                    'Could not locate instance in database,\
                     moving to end of queue'
                )
            else:
                raise DBError(
                    'instances',
                    'Failed to match instance to work. Dropping'
                )

        self.instance = self.session.query(Instance).get(existingID)

    def updateRecord(self):
        epubsToLoad = self.instance.update(self.session, self.data)

        for deferredEpub in epubsToLoad:
            self.kinesisMsgs[os.environ['EPUB_STREAM']].append({
                'data': deferredEpub,
                'recType': 'item'
            })

    def setUpdateTime(self):
        self.instance.work.date_modified = datetime.utcnow()

    def createLogger(self):
        return logger
