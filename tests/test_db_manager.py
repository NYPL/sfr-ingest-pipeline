import os
import unittest
from unittest.mock import patch, MagicMock, DEFAULT

from lib.dbManager import importRecord

class TestDBManager(unittest.TestCase):
    @patch('lib.dbManager.queryWork')
    @patch('lib.dbManager.OutputManager.putKinesis')
    @patch.dict(os.environ, {'EPUB_STREAM': 'test'})
    def test_insert_work(self, mock_put, mock_query):
        mock_uuid=MagicMock()
        mock_uuid.hex = 'newUUID'
        mock_lookup = MagicMock()
        mock_lookup.return_value = None
        mock_insert = MagicMock()
        mock_insert.return_value = ['epub1', 'epub2']
        testData = {
            'data': {
                'identifiers': []
            }
        }
        with patch.multiple('lib.dbManager.Work',
            insert=mock_insert,
            lookupWork=mock_lookup,
            uuid=mock_uuid
        ):
            testUUID = importRecord('session', testData)
            self.assertEqual(testUUID, 'newUUID')
    
    @patch('lib.dbManager.OutputManager.putKinesis')
    def test_update_work(self, mock_put):
        mock_work = MagicMock()
        mock_work.uuid.hex = 'oldUUID'
        testData = {
            'data': {
                'data': {
                    'identifiers': []
                }
            }
        }
        with patch('lib.dbManager.Work.lookupWork', return_value=mock_work):
            testReport = importRecord('session', testData)
            self.assertEqual(testReport, 'Existing work {}'.format(mock_work))
    
    @patch('lib.dbManager.Identifier.getByIdentifier', return_value=None)
    @patch('lib.dbManager.OutputManager.putKinesis')
    @patch.dict(os.environ, {'EPUB_STREAM': 'test'})
    def test_insert_instance(self, mock_put, mock_lookup):
        mock_instance = MagicMock()
        mock_instance.id = 1
        testData = {
            'type': 'instance',
            'data': {
                'identifiers': []
            }
        }
        with patch(
            'lib.dbManager.Instance.createNew',
            return_value=(mock_instance, ['epub1', 'epub2'])
        ):
            newInst = importRecord('session', testData)
            self.assertEqual(newInst, 'Instance #1')
    
    @patch('lib.dbManager.OutputManager.putKinesis')
    def test_update_instance(self, mock_put):
        testData = {
            'type': 'instance',
            'data': {
                'identifiers': []
            }
        }
        with patch('lib.dbManager.Identifier.getByIdentifier', return_value=1):
            testReport = importRecord('session', testData)
            self.assertEqual(testReport, 'Existing instance Row ID 1')
    
    @patch('lib.dbManager.Identifier.getByIdentifier', return_value=None)
    @patch('lib.dbManager.Instance.addItemRecord')
    def test_insert_item(self, mock_lookup, mock_query):
        mock_item = MagicMock()
        mock_item.id = 1
        testData = {
            'type': 'item',
            'data': {
                'identifiers': []
            }
        }
        with patch('lib.dbManager.Item.createItem', return_value=mock_item):
            newInst = importRecord('session', testData)
            self.assertEqual(newInst, 'Item #1')
    
    @patch('lib.dbManager.OutputManager.putKinesis')
    def test_update_instance(self, mock_put):
        testData = {
            'type': 'instance',
            'data': {
                'identifiers': []
            }
        }
        with patch('lib.dbManager.Identifier.getByIdentifier', return_value=1):
            testReport = importRecord('session', testData)
            self.assertEqual(testReport, 'Existing instance Row ID 1')
