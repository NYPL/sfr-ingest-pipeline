import base64
import binascii
import json
import os
from sqlalchemy.exc import OperationalError
import traceback

from helpers.errorHelpers import NoRecordsReceived, DataError, DBError
from helpers.logHelpers import createLog
from sfrCore import SessionManager
from lib.dbManager import DBUpdater
from lib.outputManager import OutputManager

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
MANAGER = SessionManager()
MANAGER.generateEngine()


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

    MANAGER.createSession()

    updater = DBUpdater(MANAGER.session)
    results = []

    try:
        for r in records:
            results.append(parseRecord(r, updater))

        logger.debug('Parsed {} records. Committing results'.format(
            str(len(results))
        ))
        MANAGER.closeConnection()
    except (NoRecordsReceived, DataError, DBError) as err:
        logger.error('Could not process records in current invocation')
        logger.debug(err)
        MANAGER.closeConnection()

    updater.sendMessages()
    return results


def parseRecord(encodedRec, updater):
    """Handles each individual record by parsing JSON from the base64 encoded
    string recieved from the Kinesis stream, creating a database session and
    inserting/updating the database to reflect this new data source. It will
    rollback changes if an error is encountered
    """
    try:
        record = json.loads(base64.b64decode(encodedRec['kinesis']['data']))
        statusCode = record['status']
        if statusCode != 200:
            if statusCode == 204:
                logger.info('No updates received')
                raise NoRecordsReceived(
                    'No records received from {}'.format(record['source']),
                    record
                )
            else:
                logger.error('Received error from pipeline')
                logger.debug(record)
                raise DataError('Received non-200 status code')
    except json.decoder.JSONDecodeError as jsonErr:
        logger.error('Invalid JSON block received')
        logger.error(jsonErr)
        raise DataError('Invalid JSON block')
    except (UnicodeDecodeError, binascii.Error) as b64Err:
        logger.error('Invalid data found in base64 encoded block')
        logger.debug(b64Err)
        raise DataError('Error in base64 encoding of record')

    try:
        MANAGER.startSession()  # Start transaction
        record = updater.importRecord(record)
        MANAGER.commitChanges()
        return record
    except OperationalError as opErr:
        MANAGER.session.rollback()  # Rollback current record only
        logger.error('Conflicting updates caused deadlock, retry')
        logger.debug(opErr)
        OutputManager.putKinesis(
            record.get('data'),
            os.environ['UPDATE_STREAM'],
            recType=record.get('type', 'work'),
        )
    except Exception as err:  # noqa: Q000
        # There are a large number of SQLAlchemy errors that can be thrown
        # These should be handled elsewhere, but this should catch anything
        # and rollback the session if we encounter something unexpected
        MANAGER.session.rollback()  # Rollback current record only
        logger.error('Failed to store record')
        logger.debug(err)
        logger.debug(traceback.format_exc())
