import unittest
from unittest.mock import patch, MagicMock

from lib.importers.coverImporter import CoverImporter
from lib.outputManager import OutputManager


class TestCoverImporter(unittest.TestCase):
    def test_ImporterInit(self):
        testImporter = CoverImporter({'data': 'data'}, 'session')
        self.assertEqual(testImporter.data, 'data')
        self.assertEqual(testImporter.session, 'session')

    def test_getIdentifier(self):
        testImporter = CoverImporter({'data': {}}, 'session')
        mockLink = MagicMock()
        mockLink.id = 1
        testImporter.link = mockLink
        self.assertEqual(testImporter.identifier, 1)

    @patch.object(CoverImporter, 'insertRecord')
    def test_lookupRecord_success(self, mockInsert):
        mockSession = MagicMock()
        testImporter = CoverImporter({'data': {}}, mockSession)
        mockSession.query().join().filter().filter().one_or_none\
            .return_value = None
        testAction = testImporter.lookupRecord()
        self.assertEqual(testAction, 'insert')
        mockInsert.assert_called_once()

    def test_lookupRecord_found(self):
        testImporter = CoverImporter({'data': {}}, MagicMock())
        testAction = testImporter.lookupRecord()
        self.assertEqual(testAction, 'existing')

    @patch.dict('os.environ', {'COVER_QUEUE': 'testQueue'})
    @patch('lib.importers.coverImporter.Link', return_value='testLink')
    @patch.object(OutputManager, 'putQueue')
    def test_insertRecord(self, mockPut, mockLink):
        mockSession = MagicMock()
        mockInstance = MagicMock()
        mockInstance.links = set()
        mockSession.query().get.return_value = mockInstance

        testImporter = CoverImporter({'data': {}}, mockSession)
        testImporter.insertRecord(1, 'testURI')

        self.assertEqual(testImporter.link, 'testLink')
        self.assertEqual(len(list(mockInstance.links)), 1)

    @patch('lib.importers.coverImporter.datetime')
    def test_setInsertTime(self, mockUTC):
        testImporter = CoverImporter({'data': {}}, 'session')
        testLink = MagicMock()
        testInstance = MagicMock()
        testInstance.work = MagicMock()
        testImporter.link = testLink
        testLink.instances = [testInstance]
        mockUTC.utcnow.return_value = 1000
        testImporter.setInsertTime()
        self.assertEqual(
            testImporter.link.instances[0].work.date_modified,
            1000
        )
