from copy import copy
from datetime import datetime
import json
import os

from .abstractUpdater import AbstractUpdater
from sfrCore import Link
from helpers.errorHelpers import DBError
from helpers.logHelpers import createLog

logger = createLog('coverUpdater')


class CoverUpdater(AbstractUpdater):
    def __init__(self, record, session, kinesisMsgs, sqsMsgs):
        self.data = record.get('data')
        self.attempts = int(record.get('attempts', 0))
        self.link = None
        self.logger = self.createLogger()
        super().__init__(record, session, kinesisMsgs, sqsMsgs)

    @property
    def identifier(self):
        return self.link.id

    def lookupRecord(self):
        currentURL = self.data.pop('originalURL', None)
        self.logger.debug('Updating Cover from {}'.format(
            currentURL if currentURL else '[unknown]'
        ))
        dbURL = Link.httpRegexSub(currentURL)
        self.link = self.session.query(Link).filter(Link.url == dbURL).first()
        if self.link is None:
            if self.attempts < 3:
                self.logger.warning(
                    """Attempt {} Could not locate link, placing at end of queue
                    """.format(
                        self.attempts + 1
                    )
                )
                self.kinesisMsgs[os.environ['UPDATE_STREAM']].append({
                    'data': self.data,
                    'recType': 'link',
                    'attempts': self.attempts + 1
                })
                raise DBError(
                    'links',
                    """Could not locate link in database, moving to end of queue
                    """
                )
            else:
                raise DBError('links', 'Failed to find link in db. Dropping')

    def updateRecord(self):
        self.link.url = self.data.get('storedURL')
        # SQLAlchemy checks if the object reference has changed, so we cannot
        # just update this object, it must be copied and then altered
        try:
            tmpFlags = copy(json.loads(self.link.flags))
        except TypeError:
            tmpFlags = copy(self.link.flags)
        tmpFlags['temporary'] = False
        self.link.flags = tmpFlags
        self.session.add(self.link)

    def setUpdateTime(self):
        if len(self.link.instances) == 0:
            raise DBError('links', 'Cover must be associated with an instance')
        self.link.instances[0].work.date_modified = datetime.utcnow()

    def createLogger(self):
        return logger
