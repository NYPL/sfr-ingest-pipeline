from abc import ABC, abstractmethod


class AbsCoverFetcher(ABC):
    """Abstract class that represents a the base methods for a cover fetcher"""
    @abstractmethod
    def queryIdentifier(self, idType, identifier):
        """Method for querying identifier for a cover image

        Arguments:
            idType {string} -- Type of identifier being queried
            identifier {string} -- Identifier to be queried

        Returns:
            [string] -- Internal identifier from fetcher source for found cover
        """
        return None

    @abstractmethod
    def createCoverURL(self, id):
        """Take the identifier generated in queryIdentifier and generate a
        resolvable URI that can be used to store the cover in SFR.

        Arguments:
            id {string} -- Identifier from the fetcher source

        Returns:
            [string] -- Resolvable URI for the cover image
        """
        return None

    @abstractmethod
    def getSource(self):
        """Return name of the fetcher source

        Returns:
            [string] -- Name of the fetcher source
        """
        return 'abstractFetcher'

    @abstractmethod
    def getMimeType(self):
        """Return the MIMETYPE of the retrieved cover file
        """
        return None
