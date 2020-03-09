import unittest
import logging
import os

from helpers.logHelpers import createLog


class TestLogger:
    def test_log_default(self):
        logger = createLog('tester')
        level = logger.getEffectiveLevel()
        assert level == logging.WARNING

    def test_log_debug(self):
        os.environ['LOG_LEVEL'] = 'debug'
        logger = createLog('tester')
        level = logger.getEffectiveLevel()
        assert level == logging.DEBUG
        del os.environ['LOG_LEVEL']

    def test_log_bad_level(self):
        os.environ['LOG_LEVEL'] = 'bad_level'
        logger = createLog('tester')
        level = logger.getEffectiveLevel()
        assert level == logging.WARNING
        del os.environ['LOG_LEVEL']
