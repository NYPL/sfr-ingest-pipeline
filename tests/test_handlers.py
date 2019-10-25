import os
from unittest.mock import patch


os.environ['DB_HOST'] = 'test'
os.environ['DB_PORT'] = '1'
os.environ['DB_NAME'] = 'test'
os.environ['DB_USER'] = 'test'
os.environ['DB_PSWD'] = 'test'
os.environ['DB_OL_NAME'] = 'olTest'

with patch('service.SessionManager'):
    with patch('service.OLSessionManager'):
        from service import handler


class TestHandler:
    def test_handler_clean(self, mocker):
        mockManager = mocker.patch('service.CoverManager')()
        mockManager.covers = []
        resp = handler({}, None)
        mockManager.getInstancesForSearch.assert_called_once()
        mockManager.getCoversForInstances.assert_called_once()
        mockManager.sendCoversToKinesis.assert_called_once()
        assert resp == []
