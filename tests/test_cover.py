from lib.cover import SFRCover


class TestSFRCover:
    def test_cover_init(self):
        testCover = SFRCover('testURI', 'testSource', 1)
        assert str(testCover) == '<Cover(uri=testURI, source=testSource)>'
        assert testCover.uri == 'testURI'
        assert testCover.source == 'testSource'
        assert testCover.instanceID == 1
