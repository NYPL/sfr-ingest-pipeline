from sfrCore import SessionManager

from lib.fetchers.openLibraryFetcher import OLSessionManager
from lib.coverManager import CoverManager
from helpers.logHelpers import createLog

# Logger can be passed name of current module
# Can also be instantiated on a class/method basis using dot notation
logger = createLog('handler')

"""This method will create the database if necessary and otherwise run any
new migrations. This is placed here because Lambdas will "freeze" any methods
that are executed before the main handler block, meaning that we can run
migrations and generate a db connection for multiple invocations, at least
until AWS decides to regenerate the container
"""
MANAGER = SessionManager()
MANAGER.generateEngine()

OL_MANAGER = OLSessionManager()
OL_MANAGER.generateEngine()


def handler(event, context):
    """Method invoked by Lambda event. Verifies that records were received and,
    if so, passes them to be parsed"""
    logger.debug('Starting Lambda Execution')

    coverManager = CoverManager(MANAGER, OL_MANAGER)
    coverManager.getInstancesForSearch()
    coverManager.getCoversForInstances()
    coverManager.sendCoversToKinesis()

    return coverManager.covers
