from datetime import datetime
import json
import os
from sfrCore import Instance, Identifier

from lib.importers.abstractImporter import AbstractImporter
from helpers.logHelpers import createLog

logger = createLog('instanceImporter')


class InstanceImporter(AbstractImporter):
    def __init__(self, record, session, kinesisMsgs, sqsMsgs):
        self.source = record.get('source', 'unknown')
        self.data = record['data']
        self.instance = None
        self.kinesisMsgs = kinesisMsgs
        self.sqsMsgs = sqsMsgs
        self.logger = self.createLogger()
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
            self.kinesisMsgs[os.environ['UPDATE_STREAM']].append({
                'recType': 'instance',
                'data': self.data
            })
            return 'update'

        self.insertRecord()
        return 'insert'

    def insertRecord(self):
        self.instance, epubsToLoad = Instance.createNew(
            self.session, self.data
        )

        self.session.add(self.instance)

        self.storeCovers()
        self.storeEpubs(epubsToLoad)

    def storeCovers(self):
        for link in self.instance.links:
            try:
                linkFlags = json.loads(link.flags)
            except TypeError:
                linkFlags = link.flags

            if linkFlags.get('cover', False) is True:
                self.sqsMsgs[os.environ['COVER_QUEUE']].append({
                    'url': link.url,
                    'source': self.source,
                    'identifier': self.data['identifiers'][0]['identifier']
                })

    def storeEpubs(self, epubsToLoad):
        for deferredEpub in epubsToLoad:
            self.kinesisMsgs[os.environ['EPUB_STREAM']].append({
                'recType': 'item',
                'data': deferredEpub
            })

    def setInsertTime(self):
        self.instance.work.date_modified = datetime.utcnow()

    def createLogger(self):
        return logger
