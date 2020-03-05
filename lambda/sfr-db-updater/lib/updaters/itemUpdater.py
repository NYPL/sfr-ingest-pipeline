from datetime import datetime
import os

from .abstractUpdater import AbstractUpdater
from sfrCore import Item
from helpers.errorHelpers import DBError
from helpers.logHelpers import createLog

logger = createLog('itemUpdater')


class ItemUpdater(AbstractUpdater):
    def __init__(self, record, session, kinesisMsgs, sqsMsgs):
        self.data = record.get('data')
        self.attempts = int(record.get('attempts', 0))
        self.item = None
        self.logger = self.createLogger()
        super().__init__(record, session, kinesisMsgs, sqsMsgs)

    @property
    def identifier(self):
        return self.item.id

    def lookupRecord(self):
        primaryID = self.data.get('primary_identifier', None)
        self.logger.debug('Ingesting Item #{}'.format(
            primaryID['identifier'] if primaryID else 'unknown'
        ))
        self.item = Item.lookup(
            self.session,
            self.data.get('identifiers', []),
            primaryID
        )

        if self.item is None:
            if self.attempts < 3:
                self.logger.warning(
                    'Attempt {} Could not locate item,\
                     placing at end of queue'.format(
                        self.attempts + 1
                    )
                )
                self.kinesisMsgs[os.environ['UPDATE_STREAM']].append({
                    'data': self.data,
                    'recType': 'item',
                    'attempts': self.attempts + 1
                })
                raise DBError(
                    'items',
                    'Could not locate item in database,\
                     moving to end of queue'
                )
            else:
                raise DBError('items', 'Failed find item in db. Dropping')

        self.data.pop('primary_identifier', None)

    def updateRecord(self):
        self.item.update(self.session, self.data)
        self.session.add(self.item)

    def setUpdateTime(self):
        self.item.instance.work.date_modified = datetime.utcnow()

    def createLogger(self):
        return logger
