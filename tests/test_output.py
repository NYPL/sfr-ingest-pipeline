import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from collections import namedtuple

from lib.outputManager import OutputManager


class OutputTest(unittest.TestCase):

    def test_connection_creation(self):
        pass
    
    def test_redis_current(self):
        OutputManager.REDIS_CLIENT.set(
            'test/value',
            datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        )
        res = OutputManager.checkRecentQueries('test/value')
        self.assertEqual(res, True)
    
    def test_redis_missing(self):
        OutputManager.REDIS_CLIENT.delete('test/value')
        res = OutputManager.checkRecentQueries('test/value')
        self.assertEqual(res, False)
    
    def test_redis_old(self):
        oldDate = datetime.utcnow() - timedelta(days=2)
        OutputManager.REDIS_CLIENT.set(
            'test/value',
            oldDate.strftime('%Y-%m-%dT%H:%M:%S')
        )
        res = OutputManager.checkRecentQueries('test/value')
        self.assertEqual(res, False)
