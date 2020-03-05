import pytest

from lib.fetchers.openLibraryFetcher import OLCoverFetcher


class TestOpenLibraryFetcher:
    @pytest.fixture
    def testOLFetcher(self, mocker):
        return OLCoverFetcher(mocker.MagicMock())

    def test_getSource(self, testOLFetcher):
        sourceName = testOLFetcher.getSource()
        assert sourceName == 'openLibrary'

    def test_queryIdentifier(self, testOLFetcher):
        testOLFetcher.session.query().join().filter().filter().first\
            .return_value = True

        testValue = testOLFetcher.queryIdentifier('test', 1)
        assert testValue is True

    def test_createCoverURL(self, testOLFetcher):
        testURL = testOLFetcher.createCoverURL((1,))
        assert testURL == 'http://covers.openlibrary.org/b/id/1-L.jpg'
