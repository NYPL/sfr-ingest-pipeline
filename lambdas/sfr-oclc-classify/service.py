import json
import base64

from helpers.errorHelpers import (
    OCLCError,
    NoRecordsReceived,
    DataError
)
from helpers.logHelpers import createLog

from lib.enhancer import enhanceRecord

# Logger can be passed name of current module
# Can also be instantiated on a class/method basis using dot notation
logger = createLog('handler')


def handler(event, context):
    """Method invoked by Lambda event. Verifies that records were received and,
    if so, passes them to be parsed"""
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
    """Simple method to parse list of records and process each entry."""
    logger.debug("Parsing Messages")
    return [ parseRecord(r) for r in records ]

def parseRecord(encodedRec):
    """Parse an individual record. Verifies that an object was able to be
    decoded from the input base64 encoded string and if so, hands this to the
    enhancer method"""
    try:
        record = json.loads(encodedRec['body'])
        return enhanceRecord(record)
    except json.decoder.JSONDecodeError as jsonErr:
        logger.error('Invalid JSON block recieved')
        logger.error(jsonErr)
        raise DataError('Malformed JSON block recieved from SQS')
    except KeyError as err:
        logger.error('Missing body attribute in SQS message')
        logger.debug(err)
        raise DataError('Body object missing from SQS message')
    except (DataError, OCLCError) as err:
        logger.error(err.message)


    return False
