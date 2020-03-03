
from helpers.logHelpers import createLog
from helpers.errorHelpers import InvalidExecutionType, VIAFError

from lib.viaf import VIAFSearch

# Logger can be passed name of current module
# Can also be instantiated on a class/method basis using dot notation
logger = createLog('handler')


def handler(event, context):
    """The central handler response to invocations from event sources. For this
    function these come from the API Gateway

    Arguments:
        event {dict} -- Dictionary containing contents of the event that
        invoked the function, primarily the payload of data to be processed.
        context {LambdaContext} -- An object containing metadata describing
        the event source and client details.

    Raises:
        InvalidExecutionType -- Raised when GET parameters are missing or are
        malformed.

    Returns:
        [dict] -- An object that is returned to the service that
        originated the API call to the API gateway.
    """
    logger.info('Starting Lambda Execution')

    logger.debug(event)

    try:
        queryName = event['queryStringParameters']['queryName']
        queryType = event['queryStringParameters'].get('queryType', None)
    except KeyError:
        logger.error('Missing required lookup name parameter')
        raise InvalidExecutionType('queryName parameter required')

    viaf = VIAFSearch(queryName, queryType)

    try:
        returnObj = viaf.query()
    except VIAFError as err:
        logger.error(err)
        returnObj = VIAFSearch.formatResponse(500, 'OCLC API Error Received')

    return returnObj
