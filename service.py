import json
import base64

from helpers.errorHelpers import NoRecordsReceived
from helpers.logHelpers import createLog

from lib.enhancer import enhanceRecord

# Logger can be passed name of current module
# Can also be instantiated on a class/method basis using dot notation
logger = createLog('handler')


def handler(event, context):

    logger.debug('Starting Lambda Execution')

    records = event.get('Records')

    if records is None:
        logger.error('Records block is missing in Kinesis Event')
        raise NoRecordsReceived('Records block missing', event)
    elif len(records) < 1:
        logger.error('Records block contains no records')
        raise NoRecordsReceived('Records block empty', event)

    # Method to be invoked goes here
    # TODO Implement oauth checking

    results = parseRecords(records)

    logger.info('Successfully invoked lambda')

    # This return will be reflected in the CloudWatch logs
    # but doesn't actually do anything
    return results

def parseRecords(records):
    logger.debug("Parsing Messages")
    results = list(map(parseRecord, records))
    return results

def parseRecord(encodedRec):
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

    status = record['status']
    stage = record['stage']
    if status != 200:
        logger.warning('Bad Record Found! Alert the Authorities')
        return False
    elif stage != 'oclc':
        logger.info('This record is not for this stage, return for further processing')
        return False

    result = enhanceRecord(record)
    return result
