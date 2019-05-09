import json
import traceback

from sfrCore import SessionManager

from helpers.errorHelpers import NoRecordsReceived, DataError, DBError, ESError
from helpers.logHelpers import createLog
from lib.dbManager import retrieveRecords
from lib.esManager import ESConnection

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

    # Process recently updated records in the database. This is adjustable, 
    # looks back N seconds to retrieve records. Frequency of runs should be
    # determined based of experience, does not need to be live
    indexRecords()

    logger.info('Successfully invoked lambda')

    # This return will be reflected in the CloudWatch logs
    # but doesn't actually do anything
    return True


def indexRecords():
    """Processes the modified database records in the given period. Records are
    retrieved from the db, transformed into the ElasticSearch model and 
    processed in batches of 100. Errors are caught and logged within the ES
    model.
    """
    logger.info('Creating connection to ElasticSearch index')
    es = ESConnection()

    logger.info('Creating postgresql session')
    session = MANAGER.createSession()

    logger.info('Loading recently updated records')
    es.generateRecords(session)
    
    logger.info('Importing final batch into ElasticSearch')
    try:
        es.processBatch()
    except ESError as err:
        logger.debug('Batch processing Error')

    logger.info('Close postgresql session')
    MANAGER.closeConnection()
