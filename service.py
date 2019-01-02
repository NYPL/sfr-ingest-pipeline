import json
import base64

from helpers.errorHelpers import NoRecordsReceived
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
    results = list(map(parseRecord, records))
    return results

def parseRecord(encodedRec):
    """Parse an individual record. Verifies that an object was able to be
    decoded from the input base64 encoded string and if so, hands this to the
    enhancer method"""
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

    result = enhanceRecord(record)
    return result
