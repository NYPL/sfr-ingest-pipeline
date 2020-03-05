from datetime import datetime, timedelta
import os
from sqlalchemy import text
from sfrCore import Instance

from .fetchers.openLibraryFetcher import OLCoverFetcher
from .fetchers.googleBooksFetcher import GBCoverFetcher
from .fetchers.contentCafeFetcher import CCCoverFetcher
from .cover import SFRCover
from .outputManager import OutputManager
from helpers.logHelpers import createLog

logger = createLog('coverManager')


class CoverManager:
    """Manager class for finding cover images for Instance records and
    returning the resulting Cover objects to the database ingest manager.

    Methods:
    getInstancesForSearch -- Retrieve cover-less Instances from the database
    getCoversForInstances -- Search fetchers for covers and generate covers
    queryFetchers -- Query defined fetchers and break if a cover is found
    getValidIDs -- Parses list of identifiers for Instance to usable types
    sendCoversToKinesis -- places covers in stream for database manager
    """
    def __init__(self, manager, olManager):
        """Initialize CoverManager with database managers and fetchers. This
        generates a logger, sets the update period and creates the array of
        fetcher objects which are used to retrieve cover URIs.

        Arguments:
            manager {engine object} -- sqlalchemy engine to main db instance
            olManager {engine object} -- sqlalchemy engine to OL data instance
        """
        self.manager = manager
        self.olManager = olManager
        self.updatePeriod = os.environ.get('UPDATE_PERIOD', 1200)
        self.logger = logger

        self.fetchers = (
            OLCoverFetcher(self.olManager.createSession()),
            GBCoverFetcher(),
            CCCoverFetcher()
        )

        self.covers = []

        self.output = OutputManager()

    def getInstancesForSearch(self):
        """Retrieves Instance records from the database that lack cover links.
        """
        session = self.manager.createSession()
        fetchPeriod = datetime.utcnow() - timedelta(
            seconds=int(self.updatePeriod)
        )
        self.logger.info('Fetching coverless instances since {}'.format(
            fetchPeriod
        ))
        instanceQuery = session.query(Instance)\
            .outerjoin(Instance.links)\
            .filter(Instance.date_modified >= fetchPeriod)\
            .group_by(Instance.id)\
            .having(text('COUNT((CAST((links.flags -> \'cover\') AS VARCHAR)) = \'true\') < 1'))  # noqa: E501

        self.instances = instanceQuery.all()

    def getCoversForInstances(self):
        """Obtains valid identifiers from the instance and passes them to the
        queryFetcher to search for a matching cover file. If found a Cover
        object is created to represent the cover and added to the list
        attribute of the manager.
        """
        for instance in self.instances:
            self.logger.debug('Fetching cover for {}'.format(instance))
            validIdentifiers = CoverManager.getValidIDs(instance.identifiers)
            self.searchInstanceIdentifiers(instance, validIdentifiers)

    def searchInstanceIdentifiers(self, instance, validIdentifiers):
        """Queries fetchers with identifiers from an individual instance. Will
        break once a cover is found and discard any remaining identifiers.

        Arguments:
            instance {object} -- ORM object for instance record
            validIdentifiers {list} -- List of identifier objects from instance
        """
        for identifier in validIdentifiers:
            self.logger.debug('Querying identifier {} ({})'.format(
                identifier['value'],
                identifier['type']
            ))
            fetcher, fetchedID = self.queryFetchers(
                identifier['type'],
                identifier['value']
            )
            if fetcher is not None:
                coverURI = fetcher.createCoverURL(fetchedID)
                source = fetcher.getSource()
                mediaType = fetcher.getMimeType()
                self.logger.info('Found cover {} from {} for {}'.format(
                    coverURI, source, instance
                ))
                self.covers.append(
                    SFRCover(coverURI, source, mediaType, instance.id))
                break

    def queryFetchers(self, idType, identifier):
        """Queries the defined fetcher classes for a cover and returns the
        first found cover (meaning that the order of the fetcher tuple is
        the order of precedence for those sources). This is returned in a tuple
        with the source if found, else None is returned.

        Arguments:
            idType {string} -- The type of identifier being queried, this
            should be limited to isbn, lccn and oclc
            identifier {string} -- Identifier being queried

        Returns:
            [tuple] -- Tuple of cover URI and source if found, otherwise
            (None, None)
        """
        for fetcher in self.fetchers:
            fetchedID = fetcher.queryIdentifier(idType, identifier)
            if fetchedID is None:
                continue

            return fetcher, fetchedID

        return None, None

    @staticmethod
    def getValidIDs(identifiers):
        """Parses the array of identifiers from a specific instance for
        identifiers that can be queried for covers. Right now only isbn, lccn
        and oclc identifiers can be queried.

        Arguments:
            identifiers {list} -- Identifiers associated with an Instance

        Returns:
            [list] -- Filtered list of Identifier objects that have type and
            value fields
        """
        validIdentifiers = []
        for iden in identifiers:
            if iden.type in ('isbn', 'lccn', 'oclc'):
                idTable = getattr(iden, iden.type)
                validIdentifiers.append({
                    'type': iden.type,
                    'value': idTable[0].value
                })

        return validIdentifiers

    def sendCoversToKinesis(self):
        """Takes the manager's list of cover objects and sends them to the
        ingest Kinesis stream, which will place them in the database and queue
        them for permanent storage in s3.
        """
        kinesisStream = os.environ['KINESIS_INGEST_STREAM']
        for cover in self.covers:
            self.logger.info('Placing cover {} in ingest stream'.format(
                cover
            ))
            self.output.putKinesis(
                vars(cover),
                kinesisStream,
                recType='cover'
            )
