import unittest
from unittest.mock import patch, MagicMock

from lib.importers.accessImporter import AccessReportImporter
from sfrCore import Item


class TestAccessImporter(unittest.TestCase):
    def test_ImporterInit(self):
        testImporter = AccessReportImporter({'data': 'data'}, 'session', {}, {})
        self.assertEqual(testImporter.data, 'data')
        self.assertEqual(testImporter.session, 'session')

    def test_getIdentifier(self):
        testImporter = AccessReportImporter({'data': {}}, 'session', {}, {})
        mockItem = MagicMock()
        mockItem.id = 1
        testImporter.item = mockItem
        self.assertEqual(testImporter.identifier, 1)

    @patch.object(AccessReportImporter, 'insertRecord', return_value='testing')
    def test_lookupRecord(self, mockInsert):
        testImporter = AccessReportImporter({'data': {}}, 'session', {}, {})
        testAction = testImporter.lookupRecord()
        self.assertEqual(testAction, 'testing')
        self.assertEqual(testImporter.item, None)
        mockInsert.assert_called_once()

    @patch.object(Item, 'addReportData')
    def test_insertRecord_success(self, mockAddData):
        mockReport = MagicMock()
        mockReport.item = 'testItem'
        mockAddData.return_value = mockReport
        mockSession = MagicMock()
        testImporter = AccessReportImporter({'data': {}}, mockSession, {}, {})
        testAction = testImporter.insertRecord()
        self.assertEqual(testAction, 'insert')
        self.assertEqual(testImporter.item, 'testItem')
        mockAddData.assert_called_once_with(mockSession, {})
        mockSession.add.assert_called_once_with(mockReport)

    @patch.object(Item, 'addReportData', return_value=None)
    def test_insertRecord_failure(self, mockAddData):
        mockSession = MagicMock()
        testImporter = AccessReportImporter({'data': {}}, mockSession, {}, {})
        testAction = testImporter.insertRecord()
        self.assertEqual(testAction, 'error')
        self.assertEqual(testImporter.item, None)
        mockAddData.assert_called_once_with(mockSession, {})
        mockSession.add.assert_not_called()

    @patch('lib.importers.accessImporter.datetime')
    def test_setInsertTime(self, mockUTC):
        testImporter = AccessReportImporter({'data': {}}, 'session', {}, {})
        testItem = MagicMock()
        testInstance = MagicMock()
        testInstance.work = MagicMock()
        testImporter.item = testItem
        testItem.instance = testInstance
        mockUTC.utcnow.return_value = 1000
        testImporter.setInsertTime()
        self.assertEqual(testImporter.item.instance.work.date_modified, 1000)
