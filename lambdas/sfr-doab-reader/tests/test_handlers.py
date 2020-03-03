import unittest
from unittest.mock import patch
import os

from service import handler, loadSingleRecord, readOAIFeed
from helpers.errorHelpers import NoRecordsReceived



class TestHandler(unittest.TestCase):
    
    def setUp(self):
        os.environ['OUTPUT_STREAM'] = 'test_stream'
    
    def tearDown(self):
        del os.environ['OUTPUT_STREAM']

    @patch('service.Loaders')
    @patch('service.readOAIFeed')
    def test_handler_clean(self, mock_read, mock_loaders):
        testRec = {
            'source': 'CloudWatch',
            'time': 'timestamp'
        }
        handler(testRec, None)
        mock_loaders.assert_called_once()
        mock_read.assert_called_once()
    
    @patch('service.Loaders')
    @patch('service.readOAIFeed')
    @patch('service.loadSingleRecord')
    def test_handler_single(self, mock_single, mock_read, mock_loaders):
        testRec = {
            'source': 'local.url',
            'url': 'test'
        }
        handler(testRec, None)
        mock_loaders.assert_called_once()
        mock_single.assert_called_once()
        mock_read.assert_not_called()
    
    @patch('service.Loaders')
    @patch('service.parseOAI', return_value=('token', 'records'))
    @patch('service.parseMARC', return_value=[('records', 1)])
    @patch('service.KinesisOutput')
    def test_load_single(self, mock_kinesis, mock_marc, mock_oai, mock_loaders):
        loadSingleRecord(mock_loaders, 'test_rels', 'test_url')
        mock_loaders.loadOAIRecord.assert_called_with('test_url')
        mock_oai.assert_called_once()
        mock_marc.assert_called_with('records', 'test_rels')
    
    @patch('service.Loaders')
    @patch('service.readOAIFeed')
    @patch('service.parseOAI', return_value=(None, ['records']))
    @patch('service.parseMARC', return_value=[('records', 1)])
    @patch('service.KinesisOutput')
    def test_read_feed(self, mock_kinesis, mock_marc, mock_oai, mock_feed, mock_loaders):
        readOAIFeed(mock_loaders, 'test_rels')
        mock_loaders.loadOAIFeed.assert_called_with(None)
        mock_oai.assert_called_once()
        mock_marc.assert_called_once()

        testOut = {
            'source': 'doab',
            'type': 'work',
            'method': 'insert',
            'data': 'records',
            'status': 200,
            'message': 'Retrieved Gutenberg Metadata'
        }
        mock_kinesis.putRecord.assert_called_with(testOut, 'test_stream', 1)
        mock_feed.assert_not_called()
    
    @patch('service.Loaders')
    @patch('service.readOAIFeed')
    @patch('service.parseOAI', return_value=('token', ['records']))
    @patch('service.parseMARC', return_value=[('records', 1)])
    @patch('service.KinesisOutput')
    def test_read_recursive(self, mock_kinesis, mock_marc, mock_oai, mock_feed, mock_loaders):
        readOAIFeed(mock_loaders, 'test_rels')
        mock_loaders.loadOAIFeed.assert_called_with(None)
        mock_oai.assert_called_once()
        mock_marc.assert_called_once()

        testOut = {
            'source': 'doab',
            'type': 'work',
            'method': 'insert',
            'data': 'records',
            'status': 200,
            'message': 'Retrieved Gutenberg Metadata'
        }
        mock_kinesis.putRecord.assert_called_with(testOut, 'test_stream', 1)
        mock_feed.assert_called_with(mock_loaders, 'test_rels', 'token')

if __name__ == '__main__':
    unittest.main()
