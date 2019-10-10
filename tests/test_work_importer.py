import json
import unittest
from unittest.mock import patch, MagicMock, DEFAULT

from lib.importers.workImporter import WorkImporter
from sfrCore import Work
from lib.outputManager import OutputManager


class TestWorkImporter(unittest.TestCase):
    @patch.object(WorkImporter, 'parseData')
    def test_ImporterInit(self, mockParser):
        mockParser.return_value = 'data'
        testImporter = WorkImporter({}, 'session')
        self.assertEqual(testImporter.data, 'data')
        self.assertEqual(testImporter.session, 'session')

    def test_WorkParseData_nonNested(self):
        outData = WorkImporter.parseData({
            'data': {
                'field1': 'jerry',
                'field2': 'hello'
            }
        })
        self.assertEqual(outData, {'field1': 'jerry', 'field2': 'hello'})

    def test_WorkParseData_nested(self):
        outData = WorkImporter.parseData({
            'data': {
                'data': {
                    'field1': 'jerry',
                    'field2': 'hello'
                }
            }
        })
        self.assertEqual(outData, {'field1': 'jerry', 'field2': 'hello'})

    def test_getIdentifier(self):
        testUpdater = WorkImporter({'data': {}}, 'session')
        testWork = MagicMock()
        testUUID = MagicMock()
        testUUID.hex = 'uuidString'
        testWork.uuid = testUUID
        testUpdater.work = testWork
        self.assertEqual(testUpdater.identifier, 'uuidString')

    @patch.object(Work, 'lookupWork', return_value=None)
    @patch.object(WorkImporter, 'insertRecord')
    def test_lookupRecord_success(self, mockInsert, mockLookup):
        testUpdater = WorkImporter({'data': {}}, 'session')
        testAction = testUpdater.lookupRecord()
        self.assertEqual(testAction, 'insert')
        self.assertEqual(testUpdater.work, None)
        mockLookup.assert_called_once_with('session', [], None)
        mockInsert.assert_called_once()

    @patch.dict('os.environ', {'UPDATE_STREAM': 'test'})
    @patch.object(Work, 'lookupWork')
    @patch.object(OutputManager, 'putKinesis')
    def test_lookupRecord_found(self, mockPut, mockLookup):
        mockWork = MagicMock()
        mockLookup.return_value = mockWork
        mockWork.uuid = MagicMock()
        testImporter = WorkImporter({'data': {}}, 'session')
        testAction = testImporter.lookupRecord()
        self.assertEqual(testAction, 'update')
        mockLookup.assert_called_once_with('session', [], None)
        mockPut.assert_called_once()

    @patch.multiple(Work, insert=DEFAULT, uuid=DEFAULT)
    @patch.multiple(WorkImporter, storeCovers=DEFAULT, storeEpubs=DEFAULT)
    @patch('lib.importers.workImporter.queryWork')
    def test_insertRecord(self, mockQuery, insert, uuid, storeCovers,
                          storeEpubs):
        testImporter = WorkImporter({'data': {}}, 'session')
        insert.return_value = ['epub1']
        testImporter.insertRecord()
        insert.assert_called_once()
        mockQuery.assert_called_once()
        storeCovers.assert_called_once()
        storeEpubs.assert_called_once_with(['epub1'])

    @patch.dict('os.environ', {'COVER_QUEUE': 'test_queue'})
    @patch.object(OutputManager, 'putQueue')
    def test_storeCovers_strFlags(self, mockPut):
        testImporter = WorkImporter({'data': {}}, 'session')
        mockWork = MagicMock()
        mockUUID = MagicMock()
        mockUUID.hex = 'test_uuid'
        mockWork.uuid = mockUUID
        mockInstance = MagicMock()
        mockWork.instances = [mockInstance]
        mockLink = MagicMock()
        mockInstance.links = [mockLink]
        mockLink.flags = json.dumps({'cover': True})
        mockLink.url = 'testing_url'
        mockItem = MagicMock()
        mockItem.source = 'testing'
        mockInstance.items = [mockItem]

        testImporter.work = mockWork

        testImporter.storeCovers()
        mockPut.assert_called_once_with(
            {
                'url': 'testing_url',
                'source': 'testing',
                'identifier': 'test_uuid'
            },
            'test_queue'
        )

    @patch.dict('os.environ', {'COVER_QUEUE': 'test_queue'})
    @patch.object(OutputManager, 'putQueue')
    def test_storeCovers_dictFlags(self, mockPut):
        testImporter = WorkImporter({'data': {}}, 'session')
        mockWork = MagicMock()
        mockUUID = MagicMock()
        mockUUID.hex = 'test_uuid'
        mockWork.uuid = mockUUID
        mockInstance = MagicMock()
        mockWork.instances = [mockInstance]
        mockLink = MagicMock()
        mockInstance.links = [mockLink]
        mockLink.flags = {'cover': True}
        mockLink.url = 'testing_url'
        mockItem = MagicMock()
        mockItem.source = 'testing'
        mockInstance.items = [mockItem]

        testImporter.work = mockWork

        testImporter.storeCovers()
        mockPut.assert_called_once_with(
            {
                'url': 'testing_url',
                'source': 'testing',
                'identifier': 'test_uuid'
            },
            'test_queue'
        )

    @patch.dict('os.environ', {'EPUB_STREAM': 'test_stream'})
    @patch.object(OutputManager, 'putKinesis')
    def test_storeEpubs(self, mockPut):
        testImporter = WorkImporter({'data': {}}, 'session')
        testImporter.storeEpubs(['epub1'])
        mockPut.assert_called_once_with('epub1', 'test_stream', recType='item')
