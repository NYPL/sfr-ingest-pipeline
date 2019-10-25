import re
import requests
from requests.exceptions import ReadTimeout
from requests_oauthlib import OAuth1
from urllib.parse import urlparse

from helpers.errorHelpers import InvalidParameter, URLFetchError
from helpers.logHelpers import createLog
from helpers.configHelpers import decryptEnvVar
from lib.s3 import s3Client


class CoverParse:
    HATHI_CLIENT_KEY = decryptEnvVar('HATHI_CLIENT_KEY')
    HATHI_CLIENT_SECRET = decryptEnvVar('HATHI_CLIENT_SECRET')
    URL_ID_REGEX = r'\/([^\/]+\.[a-zA-Z]{3,4}$)'
    HATHI_URL_ID_REGEX = r'([a-z0-9]+\.[0-9a-z]+)\/[0-9]{1,2}\?format=jpeg&v=2$'  # noqa: E501

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
            url = 'https://{}'.format(url)
        parsedURL = urlparse(url)
        if not parsedURL.scheme or not parsedURL.netloc or not parsedURL.path:
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
        authObj = None
        if 'hathitrust' in self.remoteURL:
            authObj = CoverParse.createAuth()
        try:
            imgResp = requests.get(self.remoteURL, auth=authObj, timeout=5)
        except ReadTimeout:
            raise URLFetchError(
                'URL request timed out',
                504,
                self.remoteURL
            )
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
        if 'hathitrust' in self.remoteURL:
            urlMatch = re.search(self.HATHI_URL_ID_REGEX, self.remoteURL)
            urlID = '{}.jpg'.format(urlMatch.group(1))
        else:
            urlMatch = re.search(self.URL_ID_REGEX, self.remoteURL)
            urlID = urlMatch.group(1)
        return '{}/{}_{}'.format(self.source, self.sourceID, urlID.lower())

    @classmethod
    def createAuth(cls):
        return OAuth1(
            cls.HATHI_CLIENT_KEY,
            client_secret=cls.HATHI_CLIENT_SECRET,
            signature_type='query'
        )
