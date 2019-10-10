import unittest
from unittest.mock import patch, DEFAULT

from lib.dbManager import (
    importRecord,
    WorkImporter,
    InstanceImporter,
    ItemImporter,
    AccessReportImporter
)


class TestDBManager(unittest.TestCase):
    @patch.multiple(
        WorkImporter,
        parseData=DEFAULT,
        lookupRecord=DEFAULT,
        setInsertTime=DEFAULT,
        identifier=1
    )
    def test_insert_work_insert(self, parseData, lookupRecord, setInsertTime):
        testWorkRecord = {
            'data': 'data',
            'type': 'work'
        }
        lookupRecord.return_value = 'insert'
        result = importRecord('session', testWorkRecord)
        lookupRecord.assert_called_once()
        setInsertTime.assert_called_once()
        self.assertEqual(result, 'insert WORK #1')

    @patch.multiple(
        WorkImporter,
        parseData=DEFAULT,
        lookupRecord=DEFAULT,
        setInsertTime=DEFAULT,
        identifier=1
    )
    def test_insert_work_update(self, parseData, lookupRecord, setInsertTime):
        testWorkRecord = {
            'data': 'data',
            'type': 'work'
        }
        lookupRecord.return_value = 'update'
        result = importRecord('session', testWorkRecord)
        lookupRecord.assert_called_once()
        setInsertTime.assert_not_called()
        self.assertEqual(result, 'update WORK #1')

    @patch.multiple(
        InstanceImporter,
        lookupRecord=DEFAULT,
        setInsertTime=DEFAULT,
        identifier=1
    )
    def test_insert_instance_insert(self, lookupRecord, setInsertTime):
        testInstanceRecord = {
            'data': 'data',
            'type': 'instance'
        }
        lookupRecord.return_value = 'insert'
        result = importRecord('session', testInstanceRecord)
        lookupRecord.assert_called_once()
        setInsertTime.assert_called_once()
        self.assertEqual(result, 'insert INSTANCE #1')

    @patch.multiple(
        InstanceImporter,
        lookupRecord=DEFAULT,
        setInsertTime=DEFAULT,
        identifier=1
    )
    def test_insert_instance_update(self, lookupRecord, setInsertTime):
        testInstanceRecord = {
            'data': 'data',
            'type': 'instance'
        }
        lookupRecord.return_value = 'update'
        result = importRecord('session', testInstanceRecord)
        lookupRecord.assert_called_once()
        setInsertTime.assert_not_called()
        self.assertEqual(result, 'update INSTANCE #1')

    @patch.multiple(
        ItemImporter,
        lookupRecord=DEFAULT,
        setInsertTime=DEFAULT,
        identifier=1
    )
    def test_insert_item_insert(self, lookupRecord, setInsertTime):
        testItemRecord = {
            'data': 'data',
            'type': 'item'
        }
        lookupRecord.return_value = 'insert'
        result = importRecord('session', testItemRecord)
        lookupRecord.assert_called_once()
        setInsertTime.assert_called_once()
        self.assertEqual(result, 'insert ITEM #1')

    @patch.multiple(
        ItemImporter,
        lookupRecord=DEFAULT,
        setInsertTime=DEFAULT,
        identifier=1
    )
    def test_insert_item_update(self, lookupRecord, setInsertTime):
        testItemRecord = {
            'data': 'data',
            'type': 'item'
        }
        lookupRecord.return_value = 'update'
        result = importRecord('session', testItemRecord)
        lookupRecord.assert_called_once()
        setInsertTime.assert_not_called()
        self.assertEqual(result, 'update ITEM #1')

    @patch.multiple(
        AccessReportImporter,
        lookupRecord=DEFAULT,
        setInsertTime=DEFAULT,
        identifier=1
    )
    def test_insert_report_insert(self, lookupRecord, setInsertTime):
        testAccessRecord = {
            'data': 'data',
            'type': 'access_report'
        }
        lookupRecord.return_value = 'insert'
        result = importRecord('session', testAccessRecord)
        lookupRecord.assert_called_once()
        setInsertTime.assert_called_once()
        self.assertEqual(result, 'insert ACCESS_REPORT #1')

    @patch.multiple(
        AccessReportImporter,
        lookupRecord=DEFAULT,
        setInsertTime=DEFAULT,
        identifier=1
    )
    def test_insert_report_update(self, lookupRecord, setInsertTime):
        testAccessRecord = {
            'data': 'data',
            'type': 'access_report'
        }
        lookupRecord.return_value = 'update'
        result = importRecord('session', testAccessRecord)
        lookupRecord.assert_called_once()
        setInsertTime.assert_not_called()
        self.assertEqual(result, 'update ACCESS_REPORT #1')
