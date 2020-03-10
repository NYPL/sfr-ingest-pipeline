import unittest
from unittest.mock import patch, call, MagicMock, DEFAULT
import os
import pytest
from sfrCore import SessionManager

from helpers.errorHelpers import ESError

os.environ['DB_USER'] = 'test'
os.environ['DB_PASS'] = 'test'
os.environ['DB_HOST'] = 'test'
os.environ['DB_PORT'] = '1'
os.environ['DB_NAME'] = 'test'
os.environ['ES_INDEX'] = 'test'


class TestHandler:
    @pytest.fixture
    def mockHandler(self, mocker):
        mocker.patch.multiple(SessionManager,
            generateEngine=DEFAULT,
            createSession=DEFAULT,
            closeConnection=DEFAULT,
            startSession=DEFAULT,
            commitChanges=DEFAULT,
            decryptEnvVar=DEFAULT
        )
        from service import handler, indexRecords, MANAGER
        MANAGER.session = MagicMock()
        return (handler, indexRecords)

    def test_handler_clean(self, mocker, mockHandler):
        mockIndex = mocker.patch('service.indexRecords', return_value=True)
        testRec = {
            'source': 'CloudWatch'
        }
        resp = mockHandler[0](testRec, None)
        mockIndex.assert_called_once()
        assert resp == True

    def test_parse_records_success(self, mockHandler):
        mock_es = MagicMock()
        with patch('service.ESConnection', return_value=mock_es) as mock_conn:
            mockHandler[1]()
            mock_es.generateRecords.assert_called_once()
