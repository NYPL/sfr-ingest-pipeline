from helpers.logHelpers import createLog
from lib.sourceManager import SourceManager

# Logger can be passed name of current module
# Can also be instantiated on a class/method basis using dot notation
logger = createLog('handler')


def handler(event, context):
    """Method invoked by Lambda event. Verifies that records were received and,
    if so, passes them to be parsed"""
    logger.debug('Starting Lambda Execution')

    sourceManager = SourceManager()

    logger.info('Fetching new updated records')
    sourceManager.fetchRecords()

    logger.info('Sending works to ingest stream')
    sourceManager.sendWorksToKinesis()

    return sourceManager.works
