import json
import unittest
from unittest.mock import patch, MagicMock, DEFAULT

from lib.importers.instanceImporter import InstanceImporter
from sfrCore import Instance, Identifier
from lib.outputManager import OutputManager


class TestInstanceImporter(unittest.TestCase):
    def test_ImporterInit(self):
        testImporter = InstanceImporter({'data': 'data'}, 'session')
        self.assertEqual(testImporter.data, 'data')
        self.assertEqual(testImporter.session, 'session')

    def test_getIdentifier(self):
        testImporter = InstanceImporter({'data': {}}, 'session')
        mockInstance = MagicMock()
        mockInstance.id = 1
        testImporter.instance = mockInstance
        self.assertEqual(testImporter.identifier, 1)

    @patch.object(Identifier, 'getByIdentifier', return_value=None)
    @patch.object(InstanceImporter, 'insertRecord')
    def test_lookupRecord_success(self, mockInsert, mockLookup):
        testImporter = InstanceImporter({'data': {}}, 'session')
        testAction = testImporter.lookupRecord()
        self.assertEqual(testAction, 'insert')
        self.assertEqual(testImporter.instance, None)
        mockLookup.assert_called_once_with(Instance, 'session', [])
        mockInsert.assert_called_once()

    @patch.dict('os.environ', {'UPDATE_STREAM': 'test'})
    @patch.object(Identifier, 'getByIdentifier')
    @patch.object(OutputManager, 'putKinesis')
    def test_lookupRecord_found(self, mockPut, mockLookup):
        mockLookup.return_value = 1
        testImporter = InstanceImporter({'data': {}}, 'session')
        testAction = testImporter.lookupRecord()
        self.assertEqual(testAction, 'update')
        mockLookup.assert_called_once_with(Instance, 'session', [])
        mockPut.assert_called_once()

    @patch.object(Instance, 'createNew')
    @patch.multiple(InstanceImporter, storeCovers=DEFAULT, storeEpubs=DEFAULT)
    def test_insertRecord(self, mockCreate, storeCovers, storeEpubs):
        testImporter = InstanceImporter({'data': {}}, 'session')
        mockInstance = MagicMock()
        mockCreate.return_value = (mockInstance, ['epub1'])
        testImporter.insertRecord()
        self.assertEqual(testImporter.instance, mockInstance)
        storeCovers.assert_called_once()
        storeEpubs.assert_called_once_with(['epub1'])

    @patch.dict('os.environ', {'COVER_QUEUE': 'test_queue'})
    @patch.object(OutputManager, 'putQueue')
    def test_storeCovers_dictFlags(self, mockPut):
        testImporter = InstanceImporter(
            {
                'data': {
                    'identifiers': [{'identifier': 1}]
                }
            },
            'session'
        )
        mockInstance = MagicMock()
        mockLink = MagicMock()
        mockInstance.links = [mockLink]
        mockLink.flags = json.dumps({'cover': True})
        mockLink.url = 'testing_url'
        mockItem = MagicMock()
        mockItem.source = 'testing'
        mockInstance.items = [mockItem]

        testImporter.instance = mockInstance

        testImporter.storeCovers()
        mockPut.assert_called_once_with(
            {
                'url': 'testing_url',
                'source': 'testing',
                'identifier': 1
            },
            'test_queue'
        )

    @patch.dict('os.environ', {'COVER_QUEUE': 'test_queue'})
    @patch.object(OutputManager, 'putQueue')
    def test_storeCovers_dictFlags(self, mockPut):
        testImporter = InstanceImporter(
            {
                'data': {
                    'identifiers': [{'identifier': 1}]
                },
                'source': 'testing'
            },
            'session'
        )
        mockInstance = MagicMock()
        mockLink = MagicMock()
        mockInstance.links = [mockLink]
        mockLink.flags = {'cover': True}
        mockLink.url = 'testing_url'

        testImporter.instance = mockInstance

        testImporter.storeCovers()
        mockPut.assert_called_once_with(
            {
                'url': 'testing_url',
                'source': 'testing',
                'identifier': 1
            },
            'test_queue'
        )

    @patch.dict('os.environ', {'EPUB_STREAM': 'test_stream'})
    @patch.object(OutputManager, 'putKinesis')
    def test_storeEpubs(self, mockPut):
        testImporter = InstanceImporter({'data': {}}, 'session')
        testImporter.storeEpubs(['epub1'])
        mockPut.assert_called_once_with('epub1', 'test_stream', recType='item')

    @patch('lib.importers.instanceImporter.datetime')
    def test_setInsertTime(self, mockUTC):
        testImporter = InstanceImporter({'data': {}}, 'session')
        testInstance = MagicMock()
        testInstance.work = MagicMock()
        testImporter.instance = testInstance
        mockUTC.utcnow.return_value = 1000
        testImporter.setInsertTime()
        self.assertEqual(testImporter.instance.work.date_modified, 1000)
