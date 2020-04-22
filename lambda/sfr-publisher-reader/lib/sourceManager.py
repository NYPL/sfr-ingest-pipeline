from datetime import datetime, timedelta
import inspect
import os

from .outputManager import OutputManager
from helpers.logHelpers import createLog
import lib.readers as readers

logger = createLog('sourceManager')


class SourceManager:
    """Manager class for invoking individual readers for the different sources.
    This marshalls the returned results together, ensures that they are in a
    standard format and sends the results to the ingest stream.
    """
    def __init__(self):
        """Initializes the manager with the currently defined set of readers
        for the various sources. Also creates an output manager instance for
        sending the results when complete.
        """
        self.updatePeriod = (
            datetime.utcnow()
            - timedelta(seconds=int(os.environ.get('UPDATE_PERIOD', 1200)))
        )
        self.works = []
        self.output = OutputManager()
        self.activeReaders = os.environ.get('ACTIVE_READERS', '').split(', ')
        self.readers = inspect.getmembers(readers, inspect.isclass)

    def fetchRecords(self):
        """Invokes specific readers for publishers and returns parsed works"""
        for readerModule in self.readers:
            name, readerClass = readerModule
            if name not in self.activeReaders:
                logger.info('Not currently importing from {}'.format(name))
                continue
            reader = readerClass(self.updatePeriod)
            logger.info('Fetching records from publisher {}'.format(reader.source))
            reader.collectResourceURLs()
            reader.scrapeResourcePages()
            self.works.extend(reader.works)

    def sendWorksToKinesis(self):
        """Takes the manager's list of work objects and sends them to the
        ingest Kinesis stream, which will place them in the database.
        """
        kinesisStream = os.environ['KINESIS_INGEST_STREAM']
        for work in self.works:
            logger.info('Placing work {} in ingest stream'.format(
                work 
            ))
            self.output.putKinesis(
                vars(work),
                kinesisStream,
                recType='work'
            )
