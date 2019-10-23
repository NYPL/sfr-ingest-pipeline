from random import random
from requests.exceptions import ReadTimeout
import unittest
from unittest.mock import DEFAULT, MagicMock, patch

from lib.hathiCover import HathiCover, HathiPage
from helpers.errorHelpers import URLFetchError


class TestHathiCover(unittest.TestCase):
    @patch.object(HathiCover, 'generateOAuth', return_value='oauthHelper')
    def test_HathiCover_init(self, mockOAuth):
        testHathi = HathiCover('test.1')
        self.assertEqual(testHathi.htid, 'test.1')

    @patch('lib.hathiCover.OAuth1', return_value='oauthHelper')
    def test_cover_generate_oauth(self, mockOauth):
        testHathi = HathiCover('test.1')
        testAuth = testHathi.generateOAuth()
        mockOauth.assert_called_once_with(
            None,
            client_secret=None,
            signature_type='query'
        )
        self.assertEqual(testAuth, 'oauthHelper')

    @patch('lib.hathiCover.requests')
    @patch.multiple(
        HathiCover,
        parseMETS=DEFAULT,
        getResponse=DEFAULT
    )
    def test_HathiCover_getPageFromMETS(self,
                                        mockReq, parseMETS, getResponse):
        mockResp = MagicMock()
        testHathi = HathiCover('test.1')
        mockResp.status_code = 200
        mockResp.json = MagicMock()
        getResponse.return_value = mockResp

        parseMETS.return_value = 'test_page_url'
        testURL = testHathi.getPageFromMETS()
        getResponse.assert_called_once_with(
            'None/structure/test.1?format=json&v=2'
        )
        parseMETS.assert_called_once()
        self.assertEqual(testURL, 'test_page_url')

    @patch.object(HathiCover, 'getResponse')
    def test_HathiCover_getPageFromMETS_error(self, mockReq):
        testHathi = HathiCover('test.1')

        mockResp = MagicMock()
        mockResp.status_code = 500
        mockResp.json = MagicMock()
        mockReq.return_value = mockResp

        testURL = testHathi.getPageFromMETS()
        mockReq.assert_called_once_with(
            'None/structure/test.1?format=json&v=2'
        )
        self.assertEqual(testURL, None)

    @patch('lib.hathiCover.OAuth1', return_value='oauthHelper')
    @patch.object(HathiCover, 'getPageURL', return_value='test_page')
    @patch.multiple(
        HathiPage,
        getPageNo=DEFAULT,
        parseFlags=DEFAULT,
        setScore=DEFAULT
    )
    def test_cover_parseMETS(self,
                             mockPage, mockOauth, getPageNo, parseFlags,
                             setScore):
        def createTestStruct():
            pages = []
            for i in range(25):
                pages.append({'page': i, 'score': random()})
            sortedPages = sorted(pages, key=lambda x: x['score'], reverse=True)
            testMETS = {
                'METS:structMap': {
                    'METS:div': {
                        'METS:div': pages
                    }
                }
            }
            return testMETS, sortedPages[0]

        testMETS, topPage = createTestStruct()
        setScore.side_effect = [
            p['score']
            for p in testMETS['METS:structMap']['METS:div']['METS:div']
        ]
        testHathi = HathiCover('test.1')
        testOutput = testHathi.parseMETS(testMETS)
        mockPage.assert_called_once()
        self.assertEqual(testHathi.imagePage.score, topPage['score'])
        self.assertEqual(testOutput, 'test_page')

    @patch.object(HathiCover, 'generateOAuth', return_value='oauthHelper')
    def test_HathiCover_getPageURL(self, mockOAuth):
        testHathi = HathiCover('test.1')
        mockPage = MagicMock()
        mockPage.page = 1
        testHathi.imagePage = mockPage
        testURL = testHathi.getPageURL()
        self.assertEqual(
            testURL,
            'None/volume/pageimage/test.1/1?format=jpeg&v=2'
        )

    @patch('lib.hathiCover.requests')
    @patch.object(HathiCover, 'generateOAuth', return_value='testAuth')
    def test_getResponse_success(self, mockOAuth, mockReq):
        testHathi = HathiCover('test.1')
        mockReq.get.return_value = 'testResponse'
        testResp = testHathi.getResponse('testURL')
        self.assertEqual(testResp, 'testResponse')
        mockOAuth.assert_called_once()
        mockReq.get.assert_called_with('testURL', auth='testAuth', timeout=3)

    @patch('lib.hathiCover.requests')
    @patch.object(HathiCover, 'generateOAuth', return_value='testAuth')
    def test_getResponse_timeout(self, mockOAuth, mockReq):
        testHathi = HathiCover('test.1')
        mockReq.get.side_effect = ReadTimeout
        with self.assertRaises(URLFetchError):
            testHathi.getResponse('testURL')
            mockOAuth.assert_called_once()
