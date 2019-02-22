import unittest
from unittest.mock import patch, Mock, MagicMock, call
import os

from helpers.errorHelpers import DBError, DataError

os.environ['DB_USER'] = 'test'
os.environ['DB_PASS'] = 'test'
os.environ['DB_HOST'] = 'test'
os.environ['DB_PORT'] = 'test'
os.environ['DB_NAME'] = 'test'

from lib.dbManager import dbGenerateConnection, createSession, retrieveRecords


class TestDBManager(unittest.TestCase):

    @patch('lib.dbManager.create_engine')
    def test_create_connection(self, mock_engine):
        mock_engine.dialect.has_table.return_value = True
        res = dbGenerateConnection()
        mock_engine.assert_called_once()
        self.assertIsInstance(res, MagicMock)

    @patch('lib.dbManager.sessionmaker', return_value=Mock())
    def test_create_session(self, mock_session):
        res = createSession('engine')
        mock_session.assert_called_once()
        self.assertIsInstance(res, Mock)

    @patch.dict(os.environ, {'INDEX_PERIOD': '5'})
    def test_get_records(self):
        mockSession = MagicMock()
        mockSession.query.return_value.filter.return_value.all.return_value = [
            'work1',
            'work2'
        ]
        mockES = MagicMock()
        retrieveRecords(mockSession, mockES)
        mockES.indexRecord.assert_has_calls([call('work1'), call('work2')])
