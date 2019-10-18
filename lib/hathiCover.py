import os
import requests
from requests_oauthlib import OAuth1

from helpers.configHelpers import decryptEnvVar


class HathiCover():
    HATHI_BASE_API = os.environ.get('HATHI_BASE_API', None)
    HATHI_CLIENT_KEY = decryptEnvVar(os.environ.get('HATHI_CLIENT_KEY', None))
    HATHI_CLIENT_SECRET = decryptEnvVar(os.environ.get('HATHI_CLIENT_SECRET', None))

    def __init__(self, htid):
        self.htid = htid
        self.oauth = self.generateOAuth()

    @classmethod
    def generateOAuth(cls):
        return OAuth1(
            cls.HATHI_CLIENT_KEY,
            client_secret=cls.HATHI_CLIENT_SECRET,
            signature_type='query'
        )

    def getPageFromMETS(self):
        structURL = '{}/structure/{}?format=json&v=2'.format(
            self.HATHI_BASE_API,
            self.htid
        )
        structResp = requests.get(structURL, auth=self.oauth)

        if structResp.status_code == 200:
            return self.parseMETS(structResp.json())

        return None

    def parseMETS(self, metsJson):
        structMap = metsJson['METS:structMap']

        self.pages = [
            HathiPage(page)
            for page in structMap['METS:div']['METS:div'][:25]
        ]

        self.pages.sort(key=lambda x: x.score, reverse=True)
        self.imagePage = self.pages[0]
        return self.getPageURL()

    def getPageURL(self):
        return '{}/volume/pageimage/{}/{}?format=jpeg&v=2'.format(
            self.HATHI_BASE_API,
            self.htid,
            self.imagePage.page
        )


class HathiPage():
    PAGE_FEATURES = set(
        ['FRONT_COVER', 'TITLE', 'IMAGE_ON_PAGE', 'TABLE_OF_CONTENTS']
    )

    def __init__(self, pageData):
        self.pageData = pageData
        self.page = self.getPageNo()
        self.flags = self.parseFlags()
        self.score = self.setScore()

    def getPageNo(self):
        return self.pageData.get('ORDER', 0)

    def parseFlags(self):
        flagStr = self.pageData.get('LABEL', '')
        return set(flagStr.split(', '))

    def setScore(self):
        return len(list(self.flags & self.PAGE_FEATURES))
