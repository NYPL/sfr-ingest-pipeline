import pytest
from requests.exceptions import ReadTimeout
from unittest.mock import MagicMock, DEFAULT

from lib.covers import CoverParse
from lib.resizer import CoverResizer
from helpers.errorHelpers import InvalidParameter, URLFetchError


class TestCoverParse:
    @pytest.fixture
    def testRecord(self, mocker):
        mocker.patch('lib.covers.createLog')
        return {
            'url': 'researchnow-test.nypl.org/ebooks/123.epub',
            'source': 'testing',
            'identifier': 'xxxxxx'
        }

    @pytest.fixture
    def mockRequest(self, mocker):
        mockResp = MagicMock()
        mockReq = mocker.patch('lib.covers.requests')
        mockReq.get.return_value = mockResp
        mockResp.status_code = 200
        mockResp.content = 'image_binary'
        return mockResp

    def test_CoverParseInit_success(self, testRecord):
        testParser = CoverParse(testRecord)
        assert testParser.remoteURL == 'https://{}'.format(testRecord['url'])
        assert testParser.source == testRecord['source']
        assert testParser.sourceID == testRecord['identifier']
        assert testParser.s3CoverURL is None

    def test_CoverParseInit_badURL(self, testRecord):
        testRecord['url'] = 'some non-url string'
        with pytest.raises(InvalidParameter):
            CoverParse(testRecord)

    def test_CoverParseInit_httpURL(self, testRecord):
        testRecord['url'] = 'http://{}'.format(testRecord['url'])
        testParser = CoverParse(testRecord)
        assert testParser.remoteURL == testRecord['url']
        assert testParser.source == testRecord['source']
        assert testParser.sourceID == testRecord['identifier']
        assert testParser.s3CoverURL is None

    def test_CoverParseInit_missingURL(self, testRecord):
        testRecord.pop('url')
        with pytest.raises(InvalidParameter):
            CoverParse(testRecord)

    def test_CoverParseInit_missingSourceID(self, testRecord):
        testRecord.pop('identifier')
        with pytest.raises(InvalidParameter):
            CoverParse(testRecord)

    def test_storeCover_success_new(self, mocker, testRecord, mockRequest):
        resizeMocks = mocker.patch.multiple(
            CoverResizer,
            loadOriginal=DEFAULT,
            loadImageData=DEFAULT,
            getNewDimensions=DEFAULT,
            resizeCover=DEFAULT,
            getCoverInBytes=DEFAULT
        )
        resizeMocks['getCoverInBytes'].return_value = 'image_binary'
        mockKey = mocker.patch.object(CoverParse, 'createKey')
        mockMime = mocker.patch.object(
            CoverParse, 'getMimeType', return_value='testMime'
        )
        testParser = CoverParse(testRecord)
        mockS3 = mocker.patch('lib.covers.s3Client')()
        mockS3.checkForFile.return_value = None
        mockS3.storeNewFile.return_value = 'newImageURL'
        testParser.storeCover()
        mockKey.assert_called_once()
        mockMime.assert_called_once()
        mockS3.checkForFile.assert_called_once()
        mockS3.storeNewFile.assert_called_once_with('image_binary', 'testMime')
        assert testParser.s3CoverURL == 'newImageURL'

    def test_storeCover_success_exists(self, mocker, testRecord, mockRequest):
        mockKey = mocker.patch.object(CoverParse, 'createKey')
        mockMime = mocker.patch.object(CoverParse, 'getMimeType')
        testParser = CoverParse(testRecord)
        mockS3 = mocker.patch('lib.covers.s3Client')()
        mockS3.checkForFile.return_value = 'existingImageURL'
        testParser.storeCover()
        mockKey.assert_called_once()
        mockMime.assert_called_once()
        mockS3.checkForFile.assert_called_once()
        assert testParser.s3CoverURL == 'existingImageURL'

    def test_storeCover_failure(self, testRecord, mockRequest):
        mockRequest.status_code = 500
        testParser = CoverParse(testRecord)
        with pytest.raises(URLFetchError):
            testParser.storeCover()

    def test_storeCover_failure_timeout(self, mocker, testRecord):
        mockRequest = mocker.patch('lib.covers.requests')
        mockRequest.get.side_effect = ReadTimeout
        testParser = CoverParse(testRecord)
        with pytest.raises(URLFetchError):
            testParser.storeCover()

    def test_storeCover_hathi(self, mocker, testRecord, mockRequest):
        mockKey = mocker.patch.object(CoverParse, 'createKey')
        mockMime = mocker.patch.object(CoverParse, 'getMimeType')
        testRecord['url'] = testRecord['url'].replace('ebooks', 'hathitrust')
        mockAuth = mocker.patch.object(
            CoverParse,
            'createAuth',
            return_value='auth'
        )
        testParser = CoverParse(testRecord)
        mockS3 = mocker.patch('lib.covers.s3Client')()
        mockS3.checkForFile.return_value = 'existingImageURL'
        testParser.storeCover()
        mockKey.assert_called_once()
        mockMime.assert_called_once()
        mockAuth.assert_called_once()
        mockS3.checkForFile.assert_called_once()
        assert testParser.s3CoverURL == 'existingImageURL'

    def test_createKey(self, testRecord):
        testParser = CoverParse(testRecord)
        testKey = testParser.createKey()
        assert testKey == 'testing/xxxxxx_123.epub'

    def test_createKey_hathi(self, testRecord):
        testRecord['url'] = 'hathitrust.org/pageview/test.123456/1?format=jpeg&v=2'  # noqa: E501
        testParser = CoverParse(testRecord)
        testKey = testParser.createKey()
        assert testKey == 'testing/xxxxxx_test.123456.jpg'
    
    def test_createKey_internetarchive(self, testRecord):
        testRecord['url'] = 'archive.org/services/img/test00test'
        testRecord['identifier'] = 'ia.test00test'
        testParser = CoverParse(testRecord)
        testKey = testParser.createKey()
        assert testKey == 'testing/ia.test00test_ia.test00test.jpg'
