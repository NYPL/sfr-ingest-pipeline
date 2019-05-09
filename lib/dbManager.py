import os
from datetime import datetime, timedelta

from sfrCore import Work

from helpers.logHelpers import createLog
from helpers.errorHelpers import DBError

logger = createLog('db_manager')


def retrieveRecords(session, es):
    """Retrieve all recently updated works in the SFR database and generate
    elasticsearch-dsl ORM objects.
    """
    logger.debug('Loading Records updated in last {} seconds'.format(
        os.environ['INDEX_PERIOD'])
    )
    
    fetchPeriod = datetime.utcnow() - timedelta(seconds=int(os.environ['INDEX_PERIOD']))
    works = session.query(Work).filter(Work.date_modified >= fetchPeriod).all()
    
    logger.info('Retrieved {} works for indexing'.format(len(works)))

    for w in works:
        es.indexRecord(w)
