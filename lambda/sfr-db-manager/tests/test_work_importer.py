from collections import defaultdict
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
        testImporter = WorkImporter({}, 'session', {}, {})
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
        testUpdater = WorkImporter({'data': {}}, 'session', {}, {})
        testWork = MagicMock()
        testUUID = MagicMock()
        testUUID.hex = 'uuidString'
        testWork.uuid = testUUID
        testUpdater.work = testWork
        self.assertEqual(testUpdater.identifier, 'uuidString')

    @patch.object(Work, 'lookupWork', return_value=None)
    @patch.object(WorkImporter, 'insertRecord')
    def test_lookupRecord_success(self, mockInsert, mockLookup):
        testUpdater = WorkImporter({'data': {}}, 'session', {}, {})
        testAction = testUpdater.lookupRecord()
        self.assertEqual(testAction, 'insert')
        self.assertEqual(testUpdater.work, None)
        mockLookup.assert_called_once_with('session', [], None)
        mockInsert.assert_called_once()

    @patch.dict('os.environ', {'UPDATE_STREAM': 'test'})
    @patch.object(Work, 'lookupWork')
    def test_lookupRecord_found(self, mockLookup):
        mockWork = MagicMock()
        mockLookup.return_value = mockWork
        mockUUID = MagicMock()
        mockUUID.hex = 'testUUID'
        mockWork.uuid = mockUUID
        testImporter = WorkImporter(
            {'data': {}}, 'session', defaultdict(list), defaultdict(list)
        )
        testAction = testImporter.lookupRecord()
        self.assertEqual(testAction, 'update')
        mockLookup.assert_called_once_with('session', [], None)
        self.assertEqual(testImporter.kinesisMsgs['test'][0]['data']['primary_identifier']['identifier'], 'testUUID')

    @patch.dict('os.environ', {'CLASSIFY_QUEUE': 'testQueue'})
    @patch.multiple(Work, insert=DEFAULT, uuid=DEFAULT)
    @patch.multiple(WorkImporter, storeCovers=DEFAULT, storeEpubs=DEFAULT)
    @patch('lib.importers.workImporter.queryWork')
    def test_insertRecord(self, mockQuery, insert, uuid, storeCovers,
                          storeEpubs):
        mockSession = MagicMock()
        testImporter = WorkImporter(
            {'data': {}}, mockSession, defaultdict(list), defaultdict(list))
        insert.return_value = ['epub1']
        mockQuery.return_value = ['testQueryMessage']
        testImporter.insertRecord()
        insert.assert_called_once()
        mockQuery.assert_called_once()
        storeCovers.assert_called_once()
        storeEpubs.assert_called_once_with(['epub1'])
        self.assertEqual(
            testImporter.sqsMsgs['testQueue'][0], 'testQueryMessage'
        )
        mockSession.add.assert_called_once()

    @patch.dict('os.environ', {'COVER_QUEUE': 'test_queue'})
    def test_storeCovers_strFlags(self):
        testImporter = WorkImporter(
            {'data': {}, 'source': 'test'},
            'session',
            defaultdict(list), defaultdict(list)
        )
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

        testImporter.work = mockWork

        testImporter.storeCovers()
        self.assertEqual(
            testImporter.sqsMsgs['test_queue'][0]['url'], 'testing_url'
        )

    @patch.dict('os.environ', {'COVER_QUEUE': 'test_queue'})
    def test_storeCovers_dictFlags(self):
        testImporter = WorkImporter(
            {'data': {}, 'source': 'test'}, 'session',
            defaultdict(list), defaultdict(list))
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

        testImporter.work = mockWork

        testImporter.storeCovers()
        self.assertEqual(
            testImporter.sqsMsgs['test_queue'][0]['url'], 'testing_url'
        )

    @patch.dict('os.environ', {'EPUB_STREAM': 'test_stream'})
    def test_storeEpubs(self):
        testImporter = WorkImporter(
            {'data': {}}, 'session', defaultdict(list), defaultdict(list))
        testImporter.storeEpubs(['epub1'])
        self.assertEqual(testImporter.kinesisMsgs['test_stream'][0]['data'], 'epub1')
