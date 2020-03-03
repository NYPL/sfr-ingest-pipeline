from helpers.logHelpers import createLog

from lib.outPutManager import OutputManager
from lib.recordFetch import fetchData

# Logger can be passed name of current module
# Can also be instantiated on a class/method basis using dot notation
logger = createLog('handler')


def handler(event, context):
    """Method invoked by Lambda event. Verifies that records were received and,
    if so, passes them to be parsed"""
    logger.debug('Starting Lambda Execution')
    try:
        queryIdentifier = event['queryStringParameters']['identifier']
        queryType = event['queryStringParameters']['type']
    except KeyError:
        # Return 400 error if these keys cannot be found
        return OutputManager.formatResponse(
            400,
            {'message': 'GET query must include identifier and type'}
        )

    try:
        return OutputManager.formatResponse(
            200,
            fetchData(queryIdentifier, queryType)
        )
    except Exception as err:
        # Return 500 error code for a bad execution
        return OutputManager.formatResponse(
            500,
            {'message': err.message}
        )