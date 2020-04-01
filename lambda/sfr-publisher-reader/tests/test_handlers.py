import os
import pytest
from unittest.mock import DEFAULT, patch

from service import handler, SourceManager


class TestHandler:
    def test_handler_clean(self, mocker):
        with patch.multiple(
            SourceManager,
            fetchRecords=DEFAULT,
            sendWorksToKinesis=DEFAULT
        ) as managerMocks:
            outWorks = handler({}, {})
            managerMocks['fetchRecords'].assert_called_once()
            managerMocks['sendWorksToKinesis'].assert_called_once()
            assert outWorks == []
