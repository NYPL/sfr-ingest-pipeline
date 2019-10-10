from datetime import datetime
import json
import os
from sfrCore import Instance, Identifier

from lib.importers.abstractImporter import AbstractImporter
from lib.outputManager import OutputManager


class InstanceImporter(AbstractImporter):
    def __init__(self, record, session):
        self.data = record['data']
        self.instance = None
        super().__init__(record, session)

    @property
    def identifier(self):
        return self.instance.id

    def lookupRecord(self):
        self.logger.info('Ingesting instance record')

        instanceID = Identifier.getByIdentifier(
            Instance,
            self.session,
            self.data.get('identifiers', [])
        )
        if instanceID is not None:
            self.logger.info(
                'Found existing instance {}. Placing in update stream'.format(
                    instanceID
                )
            )
            self.data['primary_identifier'] = {
                'type': 'row_id',
                'identifier': instanceID,
                'weight': 1
            }
            OutputManager.putKinesis(
                self.data,
                os.environ['UPDATE_STREAM'],
                recType='instance'
            )
            return 'update'

        self.insertRecord()
        return 'insert'

    def insertRecord(self):
        self.instance, epubsToLoad = Instance.createNew(
            self.session, self.data
        )

        self.storeCovers()
        self.storeEpubs(epubsToLoad)

    def storeCovers(self):
        for link in self.instance.links:
            try:
                linkFlags = json.loads(link.flags)
            except TypeError:
                linkFlags = link.flags

            if linkFlags.get('cover', False) is True:
                OutputManager.putQueue(
                    {
                        'url': link.url,
                        'source': self.instance.items[0].source,
                        'identifier': self.data['identifiers'][0]['identifier']
                    },
                    os.environ['COVER_QUEUE']
                )

    def storeEpubs(self, epubsToLoad):
        for deferredEpub in epubsToLoad:
            OutputManager.putKinesis(
                deferredEpub,
                os.environ['EPUB_STREAM'],
                recType='item'
            )

    def setInsertTime(self):
        self.instance.work.date_modified = datetime.utcnow()
