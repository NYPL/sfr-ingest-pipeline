from sfrCore import SessionManager

from .abstractFetcher import AbsCoverFetcher
from ..model.identifier import Identifiers
from ..model.olid import OLIDS
from helpers.logHelpers import createLog


class OLCoverFetcher(AbsCoverFetcher):
    """Cover fetcher from the OpenLibrary API. Because of strict throttles that
    OpenLibrary applies to their API this is done with a local mirror in a
    PostgreSQL database.
    """
    def __init__(self, session):
        """Initialize class with session to OpenLibrary API database

        Arguments:
            session {object} -- Database session object
        """
        self.session = session

    def getSource(self):
        """Return name of fetcher class"""
        return 'openLibrary'

    def queryIdentifier(self, idType, identifier):
        """Query OpenLibrary database for internal olid identifier of cover
        image. Return first match found if mulitples exist.

        Arguments:
            idType {string} -- Type of the identifier being queried
            identifier {string} -- Identifier being queried

        Returns:
            integer -- olid identifier to OpenLibrary cover image
        """
        return self.session.query(OLIDS.olid)\
            .join(Identifiers)\
            .filter(Identifiers.id_type == idType)\
            .filter(Identifiers.identifier == identifier)\
            .first()

    def createCoverURL(self, olid):
        """Constructs a URI from the provided olid.

        Arguments:
            olid {integer} -- Internal identifier to OpenLibrary cover

        Returns:
            string -- Resolvable URI for cover image from OpenLibrary
        """
        return 'http://covers.openlibrary.org/b/id/{}-L.jpg'.format(olid[0])

    def getMimeType(self):
        return 'image/jpeg'


class OLSessionManager(SessionManager):
    """Subclass of database manager that allows a connection to the OpenLibrary
    API database. This exists in the same instance as the same SFR database and
    therefore only needs to set its name to be accessed.
    """
    def __init__(self, user=None, pswd=None, host=None, port=None, db=None):
        super().__init__(user=user, pswd=pswd, host=host, port=port, db=db)
        self.db = db if db else OLSessionManager.decryptEnvVar('DB_OL_NAME')
        self.logger = createLog('openLibrarySessionManager')
