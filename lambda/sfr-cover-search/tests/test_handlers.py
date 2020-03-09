import os
import pytest
from unittest.mock import MagicMock, DEFAULT

from sfrCore import SessionManager


os.environ['DB_HOST'] = 'test'
os.environ['DB_PORT'] = '1'
os.environ['DB_NAME'] = 'test'
os.environ['DB_USER'] = 'test'
os.environ['DB_PSWD'] = 'test'
os.environ['DB_OL_NAME'] = 'olTest'


class TestHandler:
    @pytest.fixture
    def mockHandler(self, mocker):
        mocker.patch.multiple(SessionManager,
            generateEngine=DEFAULT,
            createSession=DEFAULT,
            closeConnection=DEFAULT,
            startSession=DEFAULT,
            commitChanges=DEFAULT
        )
        from service import handler, MANAGER, OL_MANAGER
        MANAGER.session = MagicMock()
        OL_MANAGER.session = MagicMock()
        return (handler)


    def test_handler_clean(self, mocker, mockHandler):
        mockManager = mocker.patch('service.CoverManager')()
        mockManager.covers = []
        resp = mockHandler({}, None)
        mockManager.getInstancesForSearch.assert_called_once()
        mockManager.getCoversForInstances.assert_called_once()
        mockManager.sendCoversToKinesis.assert_called_once()
        assert resp == []
