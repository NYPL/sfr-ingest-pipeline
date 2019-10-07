import json
import os

from helpers.errorHelpers import DataError, NoRecordsReceived
from helpers.logHelpers import createLog
from lib.outputs import OutputManager
from lib.covers import CoverParse

# Logger can be passed name of current module
# Can also be instantiated on a class/method basis using dot notation
logger = createLog('handler')


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

    outManager = OutputManager()

    inserts = [parseRecord(r, outManager) for r in records]

    return inserts


def parseRecord(encodedRec, outManager):
    """Parse an individual record. Verifies that an object was able to be
    decoded from the input base64 encoded string and if so, hands this to the
    enhancer method"""
    try:
        record = json.loads(encodedRec['body'])
    except json.decoder.JSONDecodeError as jsonErr:
        logger.error('Invalid JSON block received')
        logger.error(jsonErr)
        raise DataError('Malformed JSON block received from SQS')
    except KeyError as err:
        logger.error('Missing body attribute in SQS message')
        logger.debug(err)
        raise DataError('Body object missing from SQS message')

    logger.info('Storing cover from {}'.format(
        record['url']
    ))

    coverParser = CoverParse(record)
    coverParser.storeCover()

    outManager.putKinesis(
        {
            'originalURL': coverParser.remoteURL.lower(),
            'storedURL': coverParser.s3CoverURL
        },
        os.environ['DB_UPDATE_STREAM'],
        recType='cover'
    )

    return coverParser.s3CoverURL
