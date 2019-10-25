from datetime import datetime
import os
from sfrCore import Link, Instance

from lib.importers.abstractImporter import AbstractImporter
from lib.outputManager import OutputManager


class CoverImporter(AbstractImporter):
    def __init__(self, record, session):
        self.data = record['data']
        self.link = None
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
            flags={'cover': True, 'temporary': True}
        )

        self.logger.debug('Got cover link, adding to instance')
        instance.links.add(self.link)
        self.session.add(instance)

        OutputManager.putQueue(
            {
                'url': uri,
                'source': self.data.get('source', 'unknown'),
                'identifier': instanceID
            },
            os.environ['COVER_QUEUE']
        )

    def setInsertTime(self):
        self.link.instances[0].work.date_modified = datetime.utcnow()
