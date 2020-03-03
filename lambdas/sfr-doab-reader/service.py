import os

from helpers.errorHelpers import NoRecordsReceived
from helpers.logHelpers import createLog

from lib.load import Loaders
from lib.oaiParse import parseOAI
from lib.marcParse import parseMARC
from lib.kinesisOutput import KinesisOutput

# Logger can be passed name of current module
# Can also be instantiated on a class/method basis using dot notation
logger = createLog('handler')


def handler(event, context):
    """Main handler, sets invocation type. If invoked locally, read from the
    event.json file and load specific record from supplied URL. If invoked
    otherwise (generally from a CloudWatch event), gather records updated
    in the provided period and run update.
    """
    logger.debug('Starting Lambda Execution')

    # Inialize class that handles data retrieval from external URLs
    loader = Loaders()

    # Load MARC terms here so it is only done once per invocation
    # Turns out MARC authorities probably should be turned into a module
    marcRelTerms = loader.loadMARCRelators()

    if event['source'] == 'local.url':
        loadSingleRecord(loader, marcRelTerms, event['url'])
        return
    logger.debug('Loading OAI-PMH Feed from DOAB') 
    readOAIFeed(loader, marcRelTerms)

    logger.info('Successfully invoked lambda')
    return


def loadSingleRecord(loader, marcRels, singleURL):
    """Load single DOAB record from OAI-PMH feed"""
    logger.info('Loading single OAI record from URL {}'.format(singleURL))
    oaiRecord = loader.loadOAIRecord(singleURL)
    resToken, marcRecords = parseOAI(oaiRecord)
    sfrRecords = parseMARC(marcRecords, marcRels)
    for rec, doabID in sfrRecords:
        outRec = {
            'source': 'doab',
            'type': 'work',
            'method': 'insert',
            'data': rec,
            'status': 200,
            'message': 'Retrieved Gutenberg Metadata'
        }
        KinesisOutput.putRecord(outRec, os.environ['OUTPUT_STREAM'], doabID)



def readOAIFeed(loader, marcRels, resToken=None):
    """Reads OAI-PMH feed for given ingest interval (provided in the current
    environment's config file), and dispatches retrieved & parsed records for
    persistence in the database.

    This can be invoked recursively to process multiple pages of DOAB records,
    which are limited to a max of 100 records per page.
    @value loader -- Class that managers loading external resources
    @value marcRels -- Dictionary of MARC relator terms
    @value resToken -- If invoked recursively, token identifying next page
    of results to retrieve
    """
    logger.info('Loading batch of OAI-PMH records')
    oaiFeedBatch = loader.loadOAIFeed(resToken)
    
    processCount = 0
    logger.info('Parsing batch of OAI-PMH records into MARCXML records')
    resToken, marcRecords = parseOAI(oaiFeedBatch)
    processCount += len(marcRecords)

    logger.info('Parsing DOAB records into SFR data model objects')
    sfrRecords = parseMARC(marcRecords, marcRels)
    for rec, doabID in sfrRecords:
        outRec = {
            'source': 'doab',
            'type': 'work',
            'method': 'insert',
            'data': rec,
            'status': 200,
            'message': 'Retrieved Gutenberg Metadata'
        }
        KinesisOutput.putRecord(outRec, os.environ['OUTPUT_STREAM'], doabID)
    
    logger.info('Putting parsed records into {} stream'.format(
        os.environ['OUTPUT_STREAM']
    ))


    logger.info('Processed {} DOAB records'.format(str(processCount)))

    if resToken is not None:
        logger.info('Loading {} batch of OAI records'.format(resToken))
        readOAIFeed(loader, marcRels, resToken)
    
    logger.info('Processed all DOAB records')
