from datetime import datetime
import os
from sfrCore import Item, Instance, Identifier

from lib.importers.abstractImporter import AbstractImporter
from helpers.logHelpers import createLog

logger = createLog('itemImporter')


class ItemImporter(AbstractImporter):
    def __init__(self, record, session):
        self.data = record['data']
        self.item = None
        self.kinesisMsgs = kinesisMsgs
        self.sqsMsgs = sqsMsgs
        self.logger = self.createLogger()
        super().__init__(record, session)

    @property
    def identifier(self):
        return self.item.id

    def lookupRecord(self):
        self.logger.info('Ingesting item record')

        itemID = Identifier.getByIdentifier(
            Item,
            self.session,
            self.data.get('identifiers', [])
        )
        if itemID is not None:
            self.logger.info(
                'Found existing item {}. Sending to update stream'.format(
                    itemID
                )
            )
            self.data['primary_identifier'] = {
                'type': 'row_id',
                'identifier': itemID,
                'weight': 1
            }

            # Remove the instance_id so it is nor parsed by the db layer
            self.data.pop('instance_id', None)

            self.item = self.session.query(Item).get(itemID)

            OutputManager.putKinesis(
                self.data,
                os.environ['UPDATE_STREAM'],
                recType='item'
            )
            return 'update'

        self.logger.info('Ingesting item record')

        self.insertRecord()
        return 'insert'

    def insertRecord(self):
        instanceID = self.data.pop('instance_id', None)

        self.item = Item.createItem(self.session, self.data)

        self.logger.debug('Got new item record, adding to instance')
        Instance.addItemRecord(self.session, instanceID, self.item)

    def setInsertTime(self):
        self.item.instance.work.date_modified = datetime.utcnow()

    def createLogger(self):
        return logger
