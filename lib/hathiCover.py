import os
import requests
from requests_oauthlib import OAuth1

from helpers.configHelpers import decryptEnvVar


class HathiCover():
    """Manager class for finding a cover image for HathiTrust images. This is
    done by parsing a METS object obtained through the Hathi API, extracting
    the first 25 pages and scoring them based on relevancy as a cover. The
    URI to the most relevant page image is ultimately returned.
    """
    HATHI_BASE_API = os.environ.get('HATHI_BASE_API', None)
    HATHI_CLIENT_KEY = decryptEnvVar(os.environ.get('HATHI_CLIENT_KEY', ''))
    HATHI_CLIENT_SECRET = decryptEnvVar(
        os.environ.get('HATHI_CLIENT_SECRET', '')
    )

    def __init__(self, htid):
        self.htid = htid
        self.oauth = self.generateOAuth()

    @classmethod
    def generateOAuth(cls):
        """Helper method that generates an OAuth1 block that authenticates
        requests against the HathiTrust Data API. Due to the structure of the
        API this is formatted as part of the query string.

        Returns:
            [object] -- An OAuth1 authentication block
        """
        return OAuth1(
            cls.HATHI_CLIENT_KEY,
            client_secret=cls.HATHI_CLIENT_SECRET,
            signature_type='query'
        )

    def getPageFromMETS(self):
        """Query method for the best page URI from the record's METS file

        Returns:
            [uri] -- URI to the page to be used as a cover image
        """
        structURL = '{}/structure/{}?format=json&v=2'.format(
            self.HATHI_BASE_API,
            self.htid
        )
        structResp = requests.get(structURL, auth=self.oauth)

        if structResp.status_code == 200:
            return self.parseMETS(structResp.json())

        return None

    def parseMETS(self, metsJson):
        """Parser that handles the METS file, parsing the first 25 pages into
        HathiPage objects that contain a score and position. Once parsed it
        sets the "imagePage" as the page that contains the most plausibly
        relevant cover.

        Arguments:
            metsJson {object} -- METS object extracted from the JSON response

        Returns:
            [uri] -- URI to the page to be used as a cover image
        """
        structMap = metsJson['METS:structMap']

        self.pages = [
            HathiPage(page)
            for page in structMap['METS:div']['METS:div'][:25]
        ]

        self.pages.sort(key=lambda x: x.score, reverse=True)
        self.imagePage = self.pages[0]
        return self.getPageURL()

    def getPageURL(self):
        """Extracts a resolvable URI from the page selected as a cover image.
        This URI can be used to create a local copy of the cover.

        Returns:
            [uri] -- The created URI of the cover page
        """
        return '{}/volume/pageimage/{}/{}?format=jpeg&v=2'.format(
            self.HATHI_BASE_API,
            self.htid,
            self.imagePage.page
        )


class HathiPage():
    """A representation of a single page in a HathiTrust record. This contains
    some basic description of the page as well as some metadata that we derive
    from Hathi's description to rank it in terms of its suitability as a cover
    image.
    """

    # These are the "flags" that denote a potential cover page
    # They are drawn from a larger set of flags that can be attached to a page
    PAGE_FEATURES = set(
        ['FRONT_COVER', 'TITLE', 'IMAGE_ON_PAGE', 'TABLE_OF_CONTENTS']
    )

    def __init__(self, pageData):
        self.pageData = pageData
        self.page = self.getPageNo()
        self.flags = self.parseFlags()
        self.score = self.setScore()

    def getPageNo(self):
        """Extracts the current page number (from the front cover, not number
        on the page) from the METS description of the page

        Returns:
            [integer] -- The current page number
        """
        return self.pageData.get('ORDER', 0)

    def parseFlags(self):
        """Extracts the flags (in METS these are grouped under "LABEL") that
        can be used to determine the contents of a page. These are parsed from
        a comma-delimited string into a set.

        Returns:
            [set] -- Unique set of flags assigned to the page
        """
        flagStr = self.pageData.get('LABEL', '')
        return set(flagStr.split(', '))

    def setScore(self):
        """This takes the union of the flags denoted as potentially interesting
        in the class variable above and the current flags set on the page. The
        total count of the resulting set is the "score" for the page,
        essentially how many potentially interesting elements exist on it. This
        allows the HathiCover class to determine the best possible to cover
        to display.

        Returns:
            [integer] -- The score as derived from the union of the flags set
        """
        return len(list(self.flags & self.PAGE_FEATURES))
