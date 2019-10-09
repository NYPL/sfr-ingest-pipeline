from datetime import datetime
import os

from .abstractUpdater import AbstractUpdater
from sfrCore import Instance
from lib.outputManager import OutputManager
from helpers.errorHelpers import DBError


class InstanceUpdater(AbstractUpdater):
    def __init__(self, record, session):
        self.data = record.get('data')
        self.attempts = int(record.get('attempts', 0))
        self.instance = None
        super().__init__(record, session)

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
                OutputManager.putKinesis(
                    self.data,
                    os.environ['UPDATE_STREAM'],
                    recType='instance',
                    attempts=self.attempts + 1
                )
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
            OutputManager.putKinesis(
                deferredEpub,
                os.environ['EPUB_STREAM'],
                recType='item'
            )

    def setUpdateTime(self):
        self.instance.work.date_modified = datetime.utcnow()
