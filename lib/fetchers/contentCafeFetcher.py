import requests

from helpers.configHelpers import decryptEnvVar
from .abstractFetcher import AbsCoverFetcher


class CCCoverFetcher(AbsCoverFetcher):
    """Fetcher for the ContentCafe cover API. This API requires that all
    requests be authenticated and the required credentials are stored as KMS
    encrypted variables. The API only accepts isbn values.
    """
    CONTENT_CAFE_USER = decryptEnvVar('CONTENT_CAFE_USER')
    CONTENT_CAFE_PSWD = decryptEnvVar('CONTENT_CAFE_PSWD')
    CONTENT_CAFE_URL = 'http://contentcafe2.btol.com/ContentCafe/Jacket.aspx?userID={}&password={}&type=L&Value={}'  # noqa: E501

    def __init__(self):
        """Constructor method, creates the stockImage bytes."""
        self.stockImage = CCCoverFetcher.loadStockImage()

    def getSource(self):
        """Returns name: contentCafe"""
        return 'contentCafe'

    @staticmethod
    def loadStockImage():
        """This sets the stock image. If an cover is not found by the API a
        generic blank cover is returned. To filter out these covers we must
        compare the bytes of each file. This generates the bytes for the
        comparison file.
        """
        return open('./assets/stand-in-prefix.png', 'rb').read()

    def queryIdentifier(self, idType, identifier):
        """Queries the API for a cover URI

        Arguments:
            idType {string} -- Type of identifier, only accepts isbn
            identifier {string} --  Value of the identifier

        Returns:
            [string] -- URI for the cover from the ContentCafe API
        """
        if idType != 'isbn':
            return None

        coverURL = self.CONTENT_CAFE_URL.format(
            self.CONTENT_CAFE_USER,
            self.CONTENT_CAFE_PSWD,
            identifier
        )

        searchResp = requests.get(coverURL)

        if searchResp.status_code == 200:
            imageContent = searchResp.content
            if imageContent.startswith(self.stockImage):
                return None

            return coverURL

        return None

    def createCoverURL(self, volumeID):
        """ContentCafe implementation of the createCoverURL method. This
        method does nothing because the queryIdentifier returns a valid URL.

        Arguments:
            volumeID {string} -- ContentCafe URI

        Returns:
            [string] -- Unchanged ContentCafe URI
        """
        return volumeID
