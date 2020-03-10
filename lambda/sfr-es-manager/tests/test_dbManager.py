import unittest
from unittest.mock import patch, Mock, MagicMock, call
import os

from helpers.errorHelpers import DBError, DataError

os.environ['DB_USER'] = 'test'
os.environ['DB_PASS'] = 'test'
os.environ['DB_HOST'] = 'test'
os.environ['DB_PORT'] = 'test'
os.environ['DB_NAME'] = 'test'

from lib.dbManager import retrieveRecords


class TestDBManager:
    @patch.dict(os.environ, {'INDEX_PERIOD': '5', 'ES_INDEX': 'test'})
    def test_get_records(self):
        mockSession = MagicMock()
        mockSession.query.return_value.yield_per.return_value.filter.return_value.all.return_value = [
            'work1',
            'work2'
        ]
        res = list(retrieveRecords(mockSession))
        assert res == ['work1', 'work2']
