import json
import traceback

from helpers.errorHelpers import NoRecordsReceived, DataError, DBError
from helpers.logHelpers import createLog
from lib.dbManager import dbGenerateConnection, retrieveRecords, createSession, retrieveAllRecords
from lib.esManager import ESConnection
from model.rights import Rights

"""Logger can be passed name of current module
Can also be instantiated on a class/method basis using dot notation
"""
logger = createLog('handler')

"""This method will create the database if necessary and otherwise run any
new migrations. This is placed here because Lambdas will "freeze" any methods
that are executed before the main handler block, meaning that we can run
migrations and generate a db connection for multiple invocations, at least
until AWS decides to regenerate the container
"""
engine = dbGenerateConnection()


def handler(event, context):
    """Central handler invoked by Lambda trigger. Begins processing of kinesis
    stream.
    """
    logger.debug('Starting Lambda Execution')

    if event.get('source') == 'local.reindex':
        results = reindexRecords()
        return results

    records = event.get('Records')

    # Process recently updated records in the database. This is adjustable, 
    # looks back N seconds to retrieve records. Frequency of runs should be
    # determined based of experience, does not need to be live
    results = indexRecords()

    logger.info('Successfully invoked lambda')

    # This return will be reflected in the CloudWatch logs
    # but doesn't actually do anything
    return results


def indexRecords():
    """Processes the modified database records in the given period. Records are
    retrieved from the db, transformed
    """
    es = ESConnection()
    session = createSession(engine)
    retrieveRecords(session, es)
    es.processBatch()
    session.close()


def reindexRecords():

    session = createSession(engine)
    es = ESConnection()

    works = retrieveAllRecords(session)

    res = []
    for work in works:
        print("Reindexing work {}".format(work.uuid))
        es.tries = 0
        print(work.rights[0])
        indexResult = es.indexRecord(work)
        res.append(indexResult)
    
    return res
