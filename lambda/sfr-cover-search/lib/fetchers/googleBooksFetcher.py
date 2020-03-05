import requests

from .abstractFetcher import AbsCoverFetcher
from helpers.configHelpers import decryptEnvVar


class GBCoverFetcher(AbsCoverFetcher):
    """Google Books API cover fetcher"""
    GOOGLE_API_KEY = decryptEnvVar('GOOGLE_BOOKS_KEY')
    GOOGLE_BOOKS_SEARCH = 'https://www.googleapis.com/books/v1/volumes?q={}:{}&key={}'  # noqa: E501
    GOOGLE_BOOKS_VOLUME = 'https://www.googleapis.com/books/v1/volumes/{}?key={}'  # noqa: E501
    IMAGE_SIZE_ORDER = ['small', 'thumbnail', 'smallThumbnail']

    def __init__(self):
        pass

    def getSource(self):
        return 'googleBooks'

    def queryIdentifier(self, idType, identifier):
        """Makes an authenticated request against the Google Books API for a
        volume identified by the supplied identifier. If found this returns
        the identifier for the first volume found

        Arguments:
            idType {string} -- Type of the identifier to be queried
            identifier {string} --  Value of the identifier to be queried

        Returns:
            string -- Google Books Volume Identifier
        """
        searchResp = requests.get(self.GOOGLE_BOOKS_SEARCH.format(
            idType,
            identifier,
            self.GOOGLE_API_KEY
        ))
        if searchResp.status_code == 200:
            respBody = searchResp.json()
            if (
                respBody['kind'] == 'books#volumes' and respBody['totalItems']
            ) == 1:
                return respBody['items'][0]['id']

        return None

    def createCoverURL(self, volumeID):
        """Parses the Google Books metadata object for a cover URL. If found
        it takes the first size found as set in the IMAGE_SIZE_ORDER class
        variable. It first retrieves this object from the volumeID parameter

        Arguments:
            volumeID {string} -- Google Books Volume Identifier

        Returns:
            string -- Cover Image URI
        """
        volumeResp = requests.get(self.GOOGLE_BOOKS_VOLUME.format(
            volumeID,
            self.GOOGLE_API_KEY
        ))

        if volumeResp.status_code == 200:
            volBody = volumeResp.json()
            try:
                return self.getImage(volBody['volumeInfo']['imageLinks'], 0)
            except KeyError:
                pass

        return None

    @classmethod
    def getImage(cls, imageLinks, pos):
        """Recursively fetches the image link from the imageLinks array,
        returning None if no usable sizes are found.

        Arguments:
            imageLinks {list} -- List of image links found in metadata object
            pos {integer} -- Position in IMAGE_SIZE_ORDER list to look for in
            array

        Returns:
            string -- URI to cover image
        """
        try:
            return imageLinks[cls.IMAGE_SIZE_ORDER[pos]]
        except KeyError:
            return cls.getImage(imageLinks, pos + 1)
        except IndexError:
            return None

    def getMimeType(self):
        return 'image/jpeg'
