import unittest
from unittest.mock import patch, MagicMock

from lib.updaters.instanceUpdater import InstanceUpdater
from sfrCore import Instance
from lib.outputManager import OutputManager
from helpers.errorHelpers import DBError


class TestWorkUpdater(unittest.TestCase):
    def test_UpdaterInit(self):
        testUpdater = InstanceUpdater({'data': 'data'}, 'session')
        self.assertEqual(testUpdater.data, 'data')
        self.assertEqual(testUpdater.session, 'session')
        self.assertEqual(testUpdater.attempts, 0)

    def test_getIdentifier(self):
        testUpdater = InstanceUpdater({'data': {}}, 'session')
        testInstance = MagicMock()
        testInstance.id = 1
        testUpdater.instance = testInstance
        self.assertEqual(testUpdater.identifier, 1)

    @patch.object(Instance, 'lookup', return_value=1)
    def test_lookupRecord_success(self, mockLookup):
        mockSession = MagicMock()
        mockSession.query().get.return_value = 'existing_instance'
        testUpdater = InstanceUpdater({'data': {}}, mockSession)
        testUpdater.lookupRecord()
        self.assertEqual(testUpdater.instance, 'existing_instance')
        mockLookup.assert_called_once_with(mockSession, [], None, None)
        mockSession.query().get.assert_called_once_with(1)

    @patch.dict('os.environ', {'UPDATE_STREAM': 'test'})
    @patch.object(Instance, 'lookup', return_value=None)
    @patch.object(OutputManager, 'putKinesis')
    def test_lookupRecord_missing(self, mockPut, mockLookup):
        testUpdater = InstanceUpdater({'data': {}}, 'session')
        with self.assertRaises(DBError):
            testUpdater.lookupRecord()
            mockLookup.assert_called_once_with('session', [], None, None)
            mockPut.assert_called_once_with(
                {'data': {}},
                'test',
                recType='instance',
                attempts=1
            )

    @patch.object(Instance, 'lookup', return_value=None)
    def test_lookupRecord_missing_retries_exceeded(self, mockLookup):
        testUpdater = InstanceUpdater({'data': {}, 'attempts': 3}, 'session')
        with self.assertRaises(DBError):
            testUpdater.lookupRecord()
            mockLookup.assert_called_once_with('session', [], None, None)

    @patch.dict('os.environ', {'EPUB_STREAM': 'test'})
    @patch.object(OutputManager, 'putKinesis')
    def test_updateRecord(self, mockPut):
        mockInstance = MagicMock()
        mockInstance.update.return_value = ['deferred_epub']
        testUpdater = InstanceUpdater({'data': {}}, 'session')
        testUpdater.instance = mockInstance

        testUpdater.updateRecord()
        mockInstance.update.assert_called_once_with('session', {})
        mockPut.assert_called_once_with(
            'deferred_epub',
            'test',
            recType='item'
        )

    @patch('lib.updaters.instanceUpdater.datetime')
    def test_setUpdateTime(self, mockUTC):
        testUpdater = InstanceUpdater({'data': {}}, 'session')
        testInstance = MagicMock()
        testUpdater.instance = testInstance
        mockUTC.utcnow.return_value = 1000
        testUpdater.setUpdateTime()
        self.assertEqual(testUpdater.instance.work.date_modified, 1000)
