import json
import base64

from helpers.errorHelpers import NoRecordsReceived
from helpers.logHelpers import createLog
from lib.dbManager import dbGenerateConnection, importRecord, createSession

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
    results = list(map(parseRecord, records))
    return results


def parseRecord(encodedRec):
    """Handles each individual record by parsing JSON from the base64 encoded
    string recieved from the Kinesis stream, creating a database session and
    inserting/updating the database to reflect this new data source. It will
    rollback changes if an error is encountered
    """
    try:
        record = json.loads(base64.b64decode(encodedRec['kinesis']['data']))
    except json.decoder.JSONDecodeError as jsonErr:
        logger.error('Invalid JSON block recieved')
        logger.error(jsonErr)
        return False
    except UnicodeDecodeError as b64Err:
        logger.error('Invalid data found in base64 encoded block')
        logger.debug(b64Err)
        return False

    session = createSession(engine)

    try:
        result = importRecord(session, record)
        session.flush()
        session.commit()
    except Exception as err:  # noqa: Q000
        # There are a large number of SQLAlchemy errors that can be thrown
        # These should be handled elsewhere, but this should catch anything
        # and rollback the session if we encounter something unexpected
        session.rollback()
        logger.error('Failed to store record')
        logger.debug(err)
        raise DBError('unknown', 'Unable to parse/ingest record, see logs for error')
    finally:
        logger.debug('Closing Session')
        session.close()
    return result
