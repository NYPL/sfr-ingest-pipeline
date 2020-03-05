import os
from datetime import datetime, timedelta

from sfrCore import Work

from helpers.logHelpers import createLog
from helpers.errorHelpers import DBError

logger = createLog('db_manager')


def retrieveRecords(session):
    """Retrieve all recently updated works in the SFR database and generate
    elasticsearch-dsl ORM objects.
    """
    logger.debug('Loading Records updated in last {} seconds'.format(
        os.environ['INDEX_PERIOD'])
    )
    
    fetchPeriod = datetime.utcnow() - timedelta(seconds=int(os.environ['INDEX_PERIOD']))
    for workID in session.query(Work.id)\
        .yield_per(100)\
        .filter(Work.date_modified >= fetchPeriod)\
        .all():
        yield workID
