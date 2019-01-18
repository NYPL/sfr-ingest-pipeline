import unittest
from unittest.mock import patch, Mock, MagicMock
import os

from helpers.errorHelpers import DBError, DataError

os.environ['DB_USER'] = 'test'
os.environ['DB_PASS'] = 'test'
os.environ['DB_HOST'] = 'test'
os.environ['DB_PORT'] = 'test'
os.environ['DB_NAME'] = 'test'

from lib.dbManager import dbGenerateConnection, createSession, retrieveRecord


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

    def test_get_record(self):
        mockSession = MagicMock()
        mockSession.query.return_value.filter.return_value.one.return_value = True
        res = retrieveRecord(mockSession, 'work', 'uuid')
        self.assertTrue(res)

    def test_get_record_err(self):
        mockSession = MagicMock()
        mockSession.query.return_value.filter.return_value.one.side_effect = DBError('work', 'Test Error')
        with self.assertRaises(DBError):
            retrieveRecord(mockSession, 'work', 'uuid')

    def test_get_non_work(self):
        with self.assertRaises(DBError):
            retrieveRecord('session', 'instance', 'uuid')
