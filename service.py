import json
import traceback

from helpers.logHelpers import createLog
from helpers.errorHelpers import DataError, NoRecordsReceived

from sfrCore import SessionManager

from lib.clusterManager import ClusterManager
from lib.esManager import ElasticManager, ESConnection

# Logger can be passed name of current module
# Can also be instantiated on a class/method basis using dot notation
logger = createLog('handler')

"""This method will create the database if necessary and otherwise run any
new migrations. This is placed here because Lambdas will "freeze" any methods
that are executed before the main handler block, meaning that we can run
migrations and generate a db connection for multiple invocations, at least
until AWS decides to regenerate the container
"""

MANAGER = SessionManager()
MANAGER.generateEngine()


def handler(event, context):
    """Method invoked by Lambda event. Verifies that records were received and,
    if so, passes them to be parsed"""
    logger.debug('Starting Lambda Execution')

    records = event.get('Records')

    if records is None:
        logger.error('Records block is missing in SQS Message')
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
    """Simple method to parse list of records and process each entry."""
    logger.debug('Parsing Queue Messages')

    session = MANAGER.createSession()
    esConn = ESConnection()

    updates = [parseRecord(r, session) for r in records]

    MANAGER.closeConnection()

    return updates


def parseRecord(encodedRec, session):
    """Parse an individual record. Verifies that an object was able to be
    decoded from the input base64 encoded string and if so, hands this to the
    enhancer method"""
    try:
        record = json.loads(encodedRec['body'])
        logger.info('Creating editions for work {}'.format(
            record['identifier']
        ))
        clustManager = ClusterManager(record, session)
        clustManager.clusterInstances()
        
        try:
            MANAGER.startSession() # Start transaction
            clustManager.deleteExistingEditions()
            clustManager.storeEditions()
            MANAGER.commitChanges()
        except Exception as err:  # noqa: Q000
            # There are a large number of SQLAlchemy errors that can be thrown
            # These should be handled elsewhere, but this should catch anything
            # and rollback the session if we encounter something unexpected
            print(MANAGER, MANAGER.session)
            MANAGER.session.rollback() # Rollback current record only
            logger.error('Failed to store record {}'.format(
                record['identifier']
            ))
            logger.debug(err)
            logger.debug(traceback.format_exc())
            return ('failure', clustManager.work)
        

        esManager = ElasticManager(clustManager.work)
        esManager.enhanceWork()
        esManager.saveWork()
        return ('success', esManager.work)

    except json.decoder.JSONDecodeError as jsonErr:
        logger.error('Invalid JSON block received')
        logger.error(jsonErr)
        raise DataError('Malformed JSON block received from SQS')
    except KeyError as err:
        logger.error('Missing body attribute in SQS message')
        logger.debug(err)
        raise DataError('Body object missing from SQS message')
