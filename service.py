import json
import traceback

from helpers.errorHelpers import NoRecordsReceived, DataError, DBError
from helpers.logHelpers import createLog
from lib.dbManager import dbGenerateConnection, retrieveRecord, createSession, retrieveAllRecords
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

    if records is None:
        logger.error('Records block is missing in Kinesis Event')
        raise NoRecordsReceived('Records block missing', event)
    elif len(records) < 1:
        logger.error('Records block contains no records')
        raise NoRecordsReceived('Records block empty', event)

    results = parseRecords(records)

    logger.info('Successfully invoked lambda')

    # This return will be reflected in the CloudWatch logs
    # but doesn't actually do anything
    return results


def parseRecords(records):
    """Iterator for handling multiple incoming messages"""
    logger.debug('Parsing Messages')
    es = ESConnection()
    try:
        return [parseRecord(r, es) for r in records]
    except (NoRecordsReceived, DataError, DBError) as err:
        logger.error('Could not process records in current invocation')
        logger.debug(err)


def parseRecord(encodedRec, es):
    """Handles each individual record by parsing JSON the message string
    received in the SQS queue. Each message should contain a record type
    indicator along with an identifier for that record type. These fields are
    then passed to the dbManager for retrieval and indexing.
    """
    try:
        record = json.loads(encodedRec['body'])
        recordType = record['type']
        recordID = record['identifier']
    except json.decoder.JSONDecodeError as jsonErr:
        logger.error('Invalid JSON block recieved')
        logger.error(jsonErr)
        raise DataError('Malformed JSON block recieved from SQS')
    except KeyError as err:
        logger.error('Missing body attribute in SQS message')
        logger.debug(err)
        raise DataError('Body object missing from SQS message')

    session = createSession(engine)

    try:
        logger.debug('Retrieving/Storing record {} ({})'.format(
            recordID,
            recordType
        ))
        dbRec = retrieveRecord(session, recordType, recordID)
        logger.info('Indexing record {}'.format(dbRec))
        es.tries = 0
        indexResult = es.indexRecord(dbRec)
    except Exception as err:  # noqa: Q000
        # There are a large number of SQLAlchemy errors that can be thrown
        # These should be handled elsewhere, but this should catch anything
        # and rollback the session if we encounter something unexpected
        session.rollback()
        logger.error('Failed to store record')
        logger.debug(err)
        logger.debug(traceback.format_exc())
        raise DBError(
            'unknown',
            'Unable to parse/ingest record, see logs for error'
        )

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
