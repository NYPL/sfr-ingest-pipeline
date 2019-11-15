from datetime import datetime
import os

from .abstractUpdater import AbstractUpdater
from sfrCore import Item
from lib.outputManager import OutputManager
from helpers.errorHelpers import DBError


class ItemUpdater(AbstractUpdater):
    def __init__(self, record, session):
        self.data = record.get('data')
        self.attempts = int(record.get('attempts', 0))
        self.item = None
        super().__init__(record, session)

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
                OutputManager.putKinesis(
                    self.data,
                    os.environ['UPDATE_STREAM'],
                    recType='item',
                    attempts=self.attempts + 1
                )
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

    def setUpdateTime(self):
        self.item.instance.work.date_modified = datetime.utcnow()
