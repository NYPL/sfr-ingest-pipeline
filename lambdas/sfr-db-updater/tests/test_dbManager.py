import os
import unittest
from unittest.mock import patch, DEFAULT


os.environ['REDIS_HOST'] = 'test_host'

from lib.dbManager import (
    DBUpdater, WorkUpdater, InstanceUpdater, ItemUpdater, OutputManager
)  # noqa: E402


class TestManager(unittest.TestCase):
    @patch.multiple(
        WorkUpdater,
        parseData=DEFAULT,
        lookupRecord=DEFAULT,
        updateRecord=DEFAULT,
        setUpdateTime=DEFAULT,
        identifier=1
    )
    def test_update_work(self, parseData, lookupRecord,
                         updateRecord, setUpdateTime):
        testWorkRecord = {
            'data': 'data',
            'type': 'work'
        }
        testUpdater = DBUpdater('session')
        result = testUpdater.importRecord(testWorkRecord)
        lookupRecord.assert_called_once()
        updateRecord.assert_called_once()
        setUpdateTime.assert_called_once()
        self.assertEqual(result, 'WORK #1')

    @patch.multiple(
        InstanceUpdater,
        lookupRecord=DEFAULT,
        updateRecord=DEFAULT,
        setUpdateTime=DEFAULT,
        identifier=1
    )
    def test_update_instance(self, lookupRecord, updateRecord, setUpdateTime):
        testInstanceRecord = {
            'data': 'data',
            'type': 'instance'
        }
        testUpdater = DBUpdater('session')
        result = testUpdater.importRecord(testInstanceRecord)
        lookupRecord.assert_called_once()
        updateRecord.assert_called_once()
        setUpdateTime.assert_called_once()
        self.assertEqual(result, 'INSTANCE #1')

    @patch.multiple(
        ItemUpdater,
        lookupRecord=DEFAULT,
        updateRecord=DEFAULT,
        setUpdateTime=DEFAULT,
        identifier=1
    )
    def test_update_item(self, lookupRecord, updateRecord, setUpdateTime):
        testItemRecord = {
            'data': 'data',
            'type': 'item'
        }
        testUpdater = DBUpdater('session')
        result = testUpdater.importRecord(testItemRecord)
        lookupRecord.assert_called_once()
        updateRecord.assert_called_once()
        setUpdateTime.assert_called_once()
        self.assertEqual(result, 'ITEM #1')

    @patch.multiple(
        OutputManager,
        putKinesisBatch=DEFAULT,
        putQueueBatches=DEFAULT
    )
    def test_sendMessages(self, putKinesisBatch, putQueueBatches):
        testManager = DBUpdater('session')
        testManager.kinesisMsgs['testStream'] = ['rec1', 'rec2', 'rec3']
        testManager.sqsMsgs['testQueue'] = ['msg1', 'msg2', 'msg3']

        testManager.sendMessages()
        putKinesisBatch.assert_called_with(['rec1', 'rec2', 'rec3'], 'testStream')
        putQueueBatches.assert_called_with(['msg1', 'msg2', 'msg3'], 'testQueue')
