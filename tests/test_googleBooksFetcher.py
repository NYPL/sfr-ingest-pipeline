import pytest

from lib.fetchers.googleBooksFetcher import GBCoverFetcher


class TestGoogleBooksFetcher:
    @pytest.fixture
    def testGBFetcher(self):
        return GBCoverFetcher()

    @pytest.fixture
    def mockResp(self, mocker):
        return mocker.MagicMock()

    @pytest.fixture
    def mockReq(self, mockResp, mocker):
        mockReq = mocker.patch('lib.fetchers.googleBooksFetcher.requests')
        mockReq.get.return_value = mockResp

    def test_getSource(self, testGBFetcher):
        fetcherName = testGBFetcher.getSource()
        assert fetcherName == 'googleBooks'

    def test_queryIdentifier_success(self, testGBFetcher, mockReq, mockResp):
        mockResp.status_code = 200
        mockResp.json.return_value = {
            'kind': 'books#volumes',
            'totalItems': 1,
            'items': [{
                'id': 1
            }]
        }
        testID = testGBFetcher.queryIdentifier('test', 1)
        assert testID == 1

    def test_queryIdentifier_error(self, testGBFetcher, mockReq, mockResp):
        mockResp.status_code = 500
        testID = testGBFetcher.queryIdentifier('test', 1)
        assert testID is None

    def test_queryIdentifier_no_recs(self, testGBFetcher, mockReq, mockResp):
        mockResp.status_code = 200
        mockResp.json.return_value = {
            'kind': 'books#volumes',
            'totalItems': 0,
            'items': []
        }
        testID = testGBFetcher.queryIdentifier('test', 1)
        assert testID is None

    def test_createCoverURL_success(self,
                                    testGBFetcher, mockReq, mockResp, mocker):
        mockResp.status_code = 200
        mockResp.json.return_value = {
            'volumeInfo': {
                'imageLinks': ['link1', 'link2']
            }
        }
        mocker.patch.object(GBCoverFetcher, 'getImage', return_value='link1')
        coverURL = testGBFetcher.createCoverURL(1)
        assert coverURL == 'link1'

    def test_createCoverURL_req_err(self,
                                    testGBFetcher, mockReq, mockResp, mocker):
        mockResp.status_code = 500
        coverURL = testGBFetcher.createCoverURL(1)
        assert coverURL is None

    def test_createCoverURL_no_images(self,
                                      testGBFetcher, mockReq,
                                      mockResp, mocker):
        mockResp.status_code = 200
        mockResp.json.return_value = {
            'volumeInfo': {}
        }
        mocker.patch.object(GBCoverFetcher, 'getImage', return_value='link1')
        coverURL = testGBFetcher.createCoverURL(1)
        assert coverURL is None

    def test_getImage_recursive_success(self, testGBFetcher):
        testLinks = {
            'large': 'largeLink',
            'medium': 'mediumLink',
            'thumbnail': 'thumbnailLink',
            'smallThumbnail': 'smallThumbnailLink'
        }
        imageLink = GBCoverFetcher.getImage(testLinks, 0)
        assert imageLink == 'thumbnailLink'

    def test_getImage_recursive_failure(self, testGBFetcher):
        testLinks = {
            'large': 'largeLink',
            'medium': 'mediumLink'
        }
        imageLink = GBCoverFetcher.getImage(testLinks, 0)
        assert imageLink is None
