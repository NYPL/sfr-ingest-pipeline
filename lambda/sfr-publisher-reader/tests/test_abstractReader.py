import pytest

from lib.readers.abstractReader import AbsSourceReader


class TestAbstractReader:
    @pytest.fixture
    def testReader(self):
        class TestReader(AbsSourceReader):
            pass
        TestReader.__abstractmethods__ = frozenset()
        return type(
            'Dummy{}'.format(AbsSourceReader.__name__),
            (TestReader,),
            {}
        )

    def test_collectResourceURLs(self, testReader):
        testOut = testReader.collectResourceURLs(self)
        assert testOut is None

    def test_scrapeResourcePages(self, testReader):
        testOut = testReader.scrapeResourcePages(self)
        assert testOut is None

    def test_scrapeRecordMetadata(self, testReader):
        testOut = testReader.scrapeRecordMetadata(self)
        assert testOut == 'abstractReader'

    def test_transformMetadata(self, testReader):
        testOut = testReader.transformMetadata(self)
        assert testOut == None
