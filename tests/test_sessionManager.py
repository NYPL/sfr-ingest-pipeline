import unittest
from unittest.mock import patch, MagicMock

from sfrCore.lib import SessionManager

class SessionTest(unittest.TestCase):
    @patch('sfrCore.lib.sessionManager.createLog')
    def test_init_local_vars(self, mock_log):
        testManager = SessionManager(
            user='test',
            pswd='pswd',
            host='testing',
            port='1',
            db='test'
        )
        self.assertEqual(testManager.port, '1')
        self.assertEqual(testManager.engine, None)

    @patch('sfrCore.lib.sessionManager.createLog')
    def test_init_env_vars(self, mock_log):
        testManager = SessionManager()
        self.assertEqual(testManager.host, None)
        self.assertEqual(testManager.port, None)

    @patch('sfrCore.lib.sessionManager.create_engine', return_value='newEngine')
    def test_generate_engine_success(self, mock_engine):
        testManager = SessionManager()
        testManager.generateEngine()
        self.assertEqual(testManager.engine, 'newEngine')

    @patch('sfrCore.lib.sessionManager.create_engine', side_effect=Exception)
    def test_generate_engine_error(self, mock_engine):
        testManager = SessionManager()
        with self.assertRaises(Exception):
            testManager.generateEngine()

    @patch('sfrCore.lib.sessionManager.Base')
    def test_initialize_db(self, mock_base):
        testManager = SessionManager()
        mock_engine = MagicMock()
        mock_engine.dialect.has_table.return_value = None
        testManager.engine = mock_engine
        testManager.initializeDatabase()
        mock_base.metadata.create_all.assert_called_once_with(mock_engine)

    @patch('sfrCore.lib.sessionManager.sessionmaker')
    @patch.object(SessionManager, 'generateEngine')
    def test_create_session(self, mock_generate, mock_maker):
        testManager = SessionManager()
        mock_session = MagicMock()
        mock_session.return_value = 'newSession'
        mock_maker.return_value = mock_session
        newSession = testManager.createSession()
        self.assertEqual(newSession, 'newSession')
        self.assertEqual(newSession, testManager.session)

    def test_start_session(self):
        mock_session = MagicMock()
        testManager = SessionManager()
        testManager.session = mock_session
        testManager.startSession()
        mock_session.begin_nested.assert_called_once()

    def test_commit_session(self):
        mock_session = MagicMock()
        testManager = SessionManager()
        testManager.session = mock_session
        testManager.commitChanges()
        mock_session.commit.assert_called_once()

    def test_rollback_session(self):
        mock_session = MagicMock()
        testManager = SessionManager()
        testManager.session = mock_session
        testManager.rollbackChanges()
        mock_session.rollback.assert_called_once()

    @patch.object(SessionManager, 'commitChanges')
    def test_close_connection(self, mock_commit):
        mock_session = MagicMock()
        mock_engine = MagicMock()
        testManager = SessionManager()
        testManager.session = mock_session
        testManager.engine = mock_engine

        testManager.closeConnection()
        mock_commit.assert_called_once()
        mock_session.close.assert_called_once()
        mock_engine.dispose.assert_called_once()
