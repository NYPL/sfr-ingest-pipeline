import pytest

from lib.fetchers.abstractFetcher import AbsCoverFetcher


class TestAbstractFetcher:
    @pytest.fixture
    def testFetcher(self):
        class TestFetcher(AbsCoverFetcher):
            pass
        TestFetcher.__abstractmethods__ = frozenset()
        return type(
            'Dummy{}'.format(AbsCoverFetcher.__name__),
            (TestFetcher,),
            {}
        )

    def test_queryIdentifier(self, testFetcher):
        testOut = testFetcher.queryIdentifier(self, 'type', 1)
        assert testOut is None

    def test_createCoverURL(self, testFetcher):
        testOut = testFetcher.createCoverURL(self, 1)
        assert testOut is None

    def test_getSource(self, testFetcher):
        testOut = testFetcher.getSource(self)
        assert testOut == 'abstractFetcher'
