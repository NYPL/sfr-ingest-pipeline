import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from collections import namedtuple

from lib.outputManager import OutputManager


class OutputTest(unittest.TestCase):

    def test_connection_creation(self):
        pass
    
    def test_redis_current(self):
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S').encode('utf-8')
        OutputManager.REDIS_CLIENT = mock_redis
        res = OutputManager.checkRecentQueries('test/value')
        self.assertEqual(res, True)
    
    def test_redis_missing(self):
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        OutputManager.REDIS_CLIENT = mock_redis
        res = OutputManager.checkRecentQueries('test/value')
        self.assertEqual(res, False)
    
    def test_redis_old(self):
        oldDate = datetime.utcnow() - timedelta(days=2)
        mock_redis = MagicMock()
        mock_redis.get.return_value = oldDate.strftime('%Y-%m-%dT%H:%M:%S').encode('utf-8')
        OutputManager.REDIS_CLIENT = mock_redis
        res = OutputManager.checkRecentQueries('test/value')
        self.assertEqual(res, False)
