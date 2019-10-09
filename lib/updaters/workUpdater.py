from datetime import datetime
import os

from .abstractUpdater import AbstractUpdater
from sfrCore import Work
from lib.outputManager import OutputManager
from helpers.errorHelpers import DBError


class WorkUpdater(AbstractUpdater):
    def __init__(self, record, session):
        self.data = WorkUpdater.parseData(record)
        self.attempts = int(record.get('attempts', 0))
        self.work = None
        super().__init__(record, session)

    @staticmethod
    def parseData(record):
        workData = (record['data'])
        if 'data' in workData:
            workData = workData['data']
        return workData

    @property
    def identifier(self):
        return self.work.uuid.hex

    def lookupRecord(self):
        primaryID = self.data.pop('primary_identifier', None)
        self.logger.debug('Looking up Work identified by {}'.format(primaryID))
        self.work = Work.lookupWork(
            self.session,
            self.data.get('identifiers', []),
            primaryID
        )

        if not self.work:
            if self.attempts < 3:
                self.logger.warning(
                    'Attempt {} Could not locate work,\
                     placing at end of queue'.format(
                        self.attempts + 1
                    )
                )
                OutputManager.putKinesis(
                    self.data,
                    os.environ['UPDATE_STREAM'],
                    recType='work',
                    attempts=self.attempts + 1
                )
                raise DBError(
                    'works',
                    'Could not locate work in database,\
                     moving to end of queue'
                )
            else:
                raise DBError('works', 'Failed find work in db. Dropping')

    def updateRecord(self):
        epubsToLoad = self.work.update(self.data, session=self.session)

        for deferredEpub in epubsToLoad:
            OutputManager.putKinesis(
                deferredEpub,
                os.environ['EPUB_STREAM'],
                recType='item'
            )

    def setUpdateTime(self):
        self.work.date_modified = datetime.utcnow()
