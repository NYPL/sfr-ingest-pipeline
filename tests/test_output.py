import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from collections import namedtuple

from lib.outputManager import OutputManager


@patch.dict('os.environ', {'REDIS_HOST': 'redis_url'})
class OutputTest(unittest.TestCase):

    def test_connection_creation(self):
        pass
    
    @patch('redis.StrictRedis.get', return_value=(datetime.now().strftime('%Y-%m-%dT%H:%M:%S').encode('utf-8')))
    @patch('redis.StrictRedis.set')
    def test_redis_current(self, mock_set, mock_get):
        res = OutputManager.checkRecentQueries('test/value')
        self.assertTrue(res)
    
    @patch('redis.StrictRedis.get', return_value=None)
    @patch('redis.StrictRedis.set')
    def test_redis_missing(self, mock_set, mock_get):
        res = OutputManager.checkRecentQueries('test/value')
        self.assertEqual(res, False)
    
    @patch('redis.StrictRedis.get', return_value=('2000-01-01T00:00:00'.encode('utf-8')))
    @patch('redis.StrictRedis.set')
    def test_redis_old(self, mock_set, mock_get):
        res = OutputManager.checkRecentQueries('test/value')
        self.assertEqual(res, False)
