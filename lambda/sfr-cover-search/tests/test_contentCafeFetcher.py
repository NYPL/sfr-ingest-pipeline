import pytest

from lib.fetchers.contentCafeFetcher import CCCoverFetcher


class TestContentCafeFetcher:
    @pytest.fixture
    def testCCFetch(self, mocker):
        mocker.patch.object(
            CCCoverFetcher,
            'loadStockImage',
            return_value='stock'
        )
        return CCCoverFetcher()

    @pytest.fixture
    def mockResp(self, mocker):
        return mocker.MagicMock()

    @pytest.fixture
    def mockReq(self, mockResp, mocker):
        mockReq = mocker.patch('lib.fetchers.contentCafeFetcher.requests')
        mockReq.get.return_value = mockResp

    def test_getSource(self, testCCFetch):
        sourceName = testCCFetch.getSource()
        assert sourceName == 'contentCafe'

    def test_loadStockImage(self, mocker):
        mocker.patch('builtins.open', mocker.mock_open(read_data='data'))
        testImage = CCCoverFetcher.loadStockImage()
        assert testImage == 'data'

    def test_queryIdentifier_invalid_type(self, testCCFetch):
        testURL = testCCFetch.queryIdentifier('test', 1)
        assert testURL is None

    def test_queryIdentifier_success(self, testCCFetch, mockReq, mockResp):
        mockResp.status_code = 200
        mockResp.content = 'imageData'

        testURL = testCCFetch.queryIdentifier('isbn', 1)

        assert testURL == testCCFetch.CONTENT_CAFE_URL.format(
            None, None, 1
        )

    def test_queryIdentifier_stock(self, testCCFetch, mockReq, mockResp):
        mockResp.status_code = 200
        mockResp.content = 'stockImage'

        testURL = testCCFetch.queryIdentifier('isbn', 1)

        assert testURL is None

    def test_queryIdentifier_err_response(self,
                                          testCCFetch, mockReq, mockResp):
        mockResp.status_code = 500

        testURL = testCCFetch.queryIdentifier('isbn', 1)

        assert testURL is None

    def test_createCoverURL(self, testCCFetch):
        testURL = testCCFetch.createCoverURL('testURL')
        assert testURL == 'testURL'
