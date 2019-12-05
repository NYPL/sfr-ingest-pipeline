import json
import os
from sfrCore import Work

from lib.importers.abstractImporter import AbstractImporter
from lib.queryManager import queryWork
from helpers.logHelpers import createLog

logger = createLog('workImporter')


class WorkImporter(AbstractImporter):
    def __init__(self, record, session, kinesisMsgs, sqsMsgs):
        self.source = record.get('source', 'unknown')
        self.data = WorkImporter.parseData(record)
        self.work = None
        self.kinesisMsgs = kinesisMsgs
        self.sqsMsgs = sqsMsgs
        self.logger = self.createLogger()
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
        self.work = Work.lookupWork(
            self.session,
            self.data.get('identifiers', []),
            primaryID
        )
        if self.work is not None:
            self.logger.info(
                'Found existing work {}. Sending to update stream'.format(
                    self.work.uuid.hex
                )
            )
            self.data['primary_identifier'] = {
                'type': 'uuid',
                'identifier': self.work.uuid.hex,
                'weight': 1
            }

            self.kinesisMsgs[os.environ['UPDATE_STREAM']].append({
                'recType': 'work',
                'data': self.data
            })
            return 'update'

        self.insertRecord()
        return 'insert'

    def insertRecord(self):
        self.work = Work(session=self.session)
        epubsToLoad = self.work.insert(self.data)

        self.session.add(self.work)

        # Kicks off enhancement pipeline through OCLC CLassify
        queryMsgs = queryWork(self.session, self.work, self.work.uuid.hex)
        if len(queryMsgs) > 0:
            for msg in queryMsgs:
                self.sqsMsgs[os.environ['CLASSIFY_QUEUE']].append(msg)

        self.storeCovers()
        self.storeEpubs(epubsToLoad)

    def storeCovers(self):
        for instance in self.work.instances:
            for link in instance.links:
                try:
                    linkFlags = json.loads(link.flags)
                except TypeError:
                    linkFlags = link.flags

                if linkFlags.get('cover', False) is True:
                    self.sqsMsgs[os.environ['COVER_QUEUE']].append({
                        'url': link.url,
                        'source': self.source,
                        'identifier': self.work.uuid.hex
                    })

    def storeEpubs(self, epubsToLoad):
        for deferredEpub in epubsToLoad:
            self.kinesisMsgs[os.environ['EPUB_STREAM']].append({
                'recType': 'item',
                'data': deferredEpub
            })

    def setInsertTime(self):
        super().setInsertTime()

    def createLogger(self):
        return logger
