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


class TestDBManager(unittest.TestCase):

    @patch.dict(os.environ, {'INDEX_PERIOD': '5', 'ES_INDEX': 'test'})
    @patch('lib.dbManager.ESDoc')
    def test_get_records(self, mock_doc):
        mockSession = MagicMock()
        mockSession.query.return_value.filter.return_value.all.return_value = [
            'work1',
            'work2'
        ]
        mock_es = MagicMock()
        mock_work = MagicMock()
        mock_work.work = 'esWork'
        mock_doc.return_value = mock_work
        retrieveRecords(mockSession, mock_es)
        mock_es.process.assert_has_calls([call('esWork'), call('esWork')])
