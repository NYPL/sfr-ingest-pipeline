import os
import unittest
from unittest.mock import patch, DEFAULT

os.environ['REDIS_HOST'] = 'test_host'

from lib.dbManager import (
    importRecord, WorkUpdater, InstanceUpdater, ItemUpdater
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
        result = importRecord('session', testWorkRecord)
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
        result = importRecord('session', testInstanceRecord)
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
        result = importRecord('session', testItemRecord)
        lookupRecord.assert_called_once()
        updateRecord.assert_called_once()
        setUpdateTime.assert_called_once()
        self.assertEqual(result, 'ITEM #1')


if __name__ == '__main__':
    unittest.main()
