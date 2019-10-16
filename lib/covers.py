import re
import requests
from urllib.parse import urlparse

from helpers.errorHelpers import InvalidParameter, URLFetchError
from helpers.logHelpers import createLog
from lib.s3 import s3Client


class CoverParse:
    URL_ID_REGEX = r'\/([^\/]+\.[a-zA-Z]{3,4}$)'

    def __init__(self, record):
        self.logger = createLog('CoverParse')
        self.remoteURL = record.get('url', None)
        self.source = record.get('source', 'unk')
        self.sourceID = record.get('identifier', None)
        self.s3CoverURL = None

    @property
    def remoteURL(self):
        return self._remoteURL

    @remoteURL.setter
    def remoteURL(self, url):
        if not url:
            self.logger.error('URL not provided to cover ingester')
            raise InvalidParameter('URL must be supplied to CoverParse()')
        if url[:4] != 'http':
            url = 'http://{}'.format(url)
        parsedURL = urlparse(url)
        if not parsedURL.scheme or not parsedURL.netloc:
            self.logger.error('Invalid URL provided, unable to access cover')
            raise InvalidParameter('Unable to validate URL {}'.format(url))

        self._remoteURL = url

    @property
    def sourceID(self):
        return self._sourceID

    @sourceID.setter
    def sourceID(self, identifier):
        if not identifier:
            self.logger.error('Must supply unique identifier with remoteURL')
            raise InvalidParameter('Source identifier required. None provided')

        self._sourceID = identifier

    def storeCover(self):
        imgResp = requests.get(self.remoteURL)
        if imgResp.status_code != 200:
            raise URLFetchError(
                'Unable to read image at url',
                imgResp.status_code,
                self.remoteURL
            )

        coverKey = self.createKey()
        s3 = s3Client(coverKey)
        existingFile = s3.checkForFile()
        if existingFile is None:
            self.s3CoverURL = s3.storeNewFile(imgResp.content)
        else:
            self.s3CoverURL = existingFile

    def createKey(self):
        urlMatch = re.search(self.URL_ID_REGEX, self.remoteURL)
        urlID = urlMatch.group(1)
        return '{}/{}_{}'.format(self.source, self.sourceID, urlID.lower())
