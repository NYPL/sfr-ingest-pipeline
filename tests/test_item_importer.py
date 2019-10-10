import unittest
from unittest.mock import patch, MagicMock

from lib.importers.itemImporter import ItemImporter
from sfrCore import Instance, Identifier, Item
from lib.outputManager import OutputManager


class TestItemImporter(unittest.TestCase):
    def test_ImporterInit(self):
        testImporter = ItemImporter({'data': 'data'}, 'session')
        self.assertEqual(testImporter.data, 'data')
        self.assertEqual(testImporter.session, 'session')

    def test_getIdentifier(self):
        testImporter = ItemImporter({'data': {}}, 'session')
        mockItem = MagicMock()
        mockItem.id = 1
        testImporter.item = mockItem
        self.assertEqual(testImporter.identifier, 1)

    @patch.object(Identifier, 'getByIdentifier', return_value=None)
    @patch.object(ItemImporter, 'insertRecord')
    def test_lookupRecord_success(self, mockInsert, mockLookup):
        testImporter = ItemImporter({'data': {}}, 'session')
        testAction = testImporter.lookupRecord()
        self.assertEqual(testAction, 'insert')
        self.assertEqual(testImporter.item, None)
        mockLookup.assert_called_once_with(Item, 'session', [])
        mockInsert.assert_called_once()

    @patch.dict('os.environ', {'UPDATE_STREAM': 'test'})
    @patch.object(Identifier, 'getByIdentifier')
    @patch.object(OutputManager, 'putKinesis')
    def test_lookupRecord_found(self, mockPut, mockLookup):
        mockLookup.return_value = 1
        testImporter = ItemImporter({'data': {}}, 'session')
        testAction = testImporter.lookupRecord()
        self.assertEqual(testAction, 'update')
        mockLookup.assert_called_once_with(Item, 'session', [])
        mockPut.assert_called_once()

    @patch.object(Item, 'createItem')
    @patch.object(Instance, 'addItemRecord')
    def test_insertRecord(self, mockAddItem, mockCreate):
        testImporter = ItemImporter({'data': {}}, 'session')
        mockCreate.return_value = 'testItem'
        testImporter.insertRecord()
        self.assertEqual(testImporter.item, 'testItem')
        mockAddItem.assert_called_once_with('session', None, 'testItem')

    @patch('lib.importers.itemImporter.datetime')
    def test_setInsertTime(self, mockUTC):
        testImporter = ItemImporter({'data': {}}, 'session')
        testItem = MagicMock()
        testInstance = MagicMock()
        testInstance.work = MagicMock()
        testImporter.item = testItem
        testItem.instance = testInstance
        mockUTC.utcnow.return_value = 1000
        testImporter.setInsertTime()
        self.assertEqual(testImporter.item.instance.work.date_modified, 1000)
