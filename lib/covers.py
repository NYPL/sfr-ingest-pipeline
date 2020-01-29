from mimetypes import guess_type
import re
import requests
from requests.exceptions import ReadTimeout
from requests_oauthlib import OAuth1
from urllib.parse import urlparse

from helpers.errorHelpers import InvalidParameter, URLFetchError
from helpers.logHelpers import createLog
from helpers.configHelpers import decryptEnvVar
from lib.s3 import s3Client
from lib.resizer import CoverResizer

LOGGER = createLog('CoverParse')


class CoverParse:
    HATHI_CLIENT_KEY = decryptEnvVar('HATHI_CLIENT_KEY')
    HATHI_CLIENT_SECRET = decryptEnvVar('HATHI_CLIENT_SECRET')
    URL_ID_REGEX = r'\/([^\/]+\.[a-zA-Z]{3,4}$)'
    HATHI_URL_ID_REGEX = r'([a-z0-9]+\.[$0-9a-z]+)\/[0-9]{1,2}\?format=jpeg&v=2$'  # noqa: E501
    GOOGLE_URL_ID_REGEX = r'\/[^\/]+\?id=([0-9a-zA-Z]+)\S+imgtk=[a-zA-Z_\-0-9]+&source=gbs_api$'  # noqa: E501

    def __init__(self, record):
        self.logger = LOGGER
        self.source = record.get('source', 'unk')
        self.sourceID = record.get('identifier', None)
        self.originalURL = record.get('url', None)
        self.remoteURL = record.get('url', None)
        self.s3CoverURL = None
        self.logger.debug('Source: {}|ID: {}|URL: {}'.format(
            self.source, self.sourceID, self.remoteURL
        ))

    @property
    def remoteURL(self):
        return self._remoteURL

    @remoteURL.setter
    def remoteURL(self, url):
        if not url:
            self.logger.error(
                'URL not provided from {}({}) to cover ingester'.format(
                    self.sourceID, self.source
                )
            )
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
        mimeType = self.getMimeType(coverKey)
        s3 = s3Client(coverKey)
        existingFile = s3.checkForFile()
        if existingFile is None:
            resizer = CoverResizer(imgResp.content)
            resizer.getNewDimensions()
            resizer.resizeCover()
            standardCoverBytes = resizer.getCoverInBytes()
            self.s3CoverURL = s3.storeNewFile(standardCoverBytes, mimeType)
        else:
            self.s3CoverURL = existingFile

    def createKey(self):
        if 'hathitrust' in self.remoteURL:
            urlMatch = re.search(self.HATHI_URL_ID_REGEX, self.remoteURL)
            urlID = '{}.jpg'.format(urlMatch.group(1))
        elif 'google' in self.remoteURL:
            urlMatch = re.search(self.GOOGLE_URL_ID_REGEX, self.remoteURL)
            urlID = '{}.jpg'.format(urlMatch.group(1))
        elif 'contentcafe2' in self.remoteURL:
            urlID = '{}.jpg'.format(self.sourceID)
        else:
            urlMatch = re.search(self.URL_ID_REGEX, self.remoteURL)
            urlID = urlMatch.group(1)
        return '{}/{}_{}'.format(self.source, self.sourceID, urlID.lower())

    def getMimeType(self, key):
        return guess_type(key)[0]

    @classmethod
    def createAuth(cls):
        return OAuth1(
            cls.HATHI_CLIENT_KEY,
            client_secret=cls.HATHI_CLIENT_SECRET,
            signature_type='query'
        )
