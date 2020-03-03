from datetime import datetime
import os
from sfrCore import Link, Instance

from lib.importers.abstractImporter import AbstractImporter
from helpers.logHelpers import createLog

logger = createLog('coverImporter')


class CoverImporter(AbstractImporter):
    def __init__(self, record, session, kinesisMsgs, sqsMsgs):
        self.data = record['data']
        self.link = None
        self.kinesisMsgs = kinesisMsgs
        self.sqsMsgs = sqsMsgs
        self.logger = self.createLogger()
        super().__init__(record, session)

    @property
    def identifier(self):
        return self.link.id

    def lookupRecord(self):
        self.logger.info('Ingesting cover record')
        instanceID = self.data.pop('instanceID', None)
        uri = self.data.pop('uri', None)

        coverLink = self.session.query(Link)\
            .join(Link.instances)\
            .filter(Instance.id == instanceID)\
            .filter(Link.url == uri)\
            .one_or_none()

        if coverLink is not None:
            return 'existing'

        self.logger.info('Ingesting cover link record at {}'.format(uri))

        self.insertRecord(instanceID, uri)
        return 'insert'

    def insertRecord(self, instanceID, uri):
        instance = self.session.query(Instance).get(instanceID)

        self.link = Link(
            url=uri,
            media_type=self.data.get('mediaType', None),
            flags={'cover': True, 'temporary': True}
        )

        self.logger.debug('Got cover link, adding to instance')
        instance.links.add(self.link)
        self.session.add(instance)

        self.sqsMsgs[os.environ['COVER_QUEUE']].append({
            'url': uri,
            'source': self.data.get('source', 'unknown'),
            'identifier': instanceID
        })

    def setInsertTime(self):
        self.link.instances[0].work.date_modified = datetime.utcnow()

    def createLogger(self):
        return logger
