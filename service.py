import json
import base64

from helpers.errorHelpers import NoRecordsReceived
from helpers.logHelpers import createLog
from lib.dbManager import dbGenerateConnection, importRecord, createSession

from model.work import Work
from model.altTitle import AltTitle
from model.subject import Subject
from model.instance import Instance
from model.item import Item, AccessReport
from model.link import Link
from model.measurement import Measurement
from model.agent import Agent, Alias
from model.identifiers import Identifier, OCLC, Gutenberg, LCCN, ISBN, ISSN, OWI

# Logger can be passed name of current module
# Can also be instantiated on a class/method basis using dot notation
logger = createLog('handler')

# This method will create the database if necessary and otherwise run any
# new migrations. This is placed here because Lambdas will "freeze" any methods
# that are executed before the main handler block, meaning that we can run
# migrations and generate a db connection for multiple invocations, at least
# until AWS decides to regenerate the container
engine = dbGenerateConnection()

def handler(event, context):

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

    session = createSession(engine)

    try:
        result = importRecord(session, record)
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
    
    return result
