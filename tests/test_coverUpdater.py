import os
import unittest
from unittest.mock import patch, MagicMock

from helpers.errorHelpers import DBError

os.environ['REDIS_HOST'] = 'test_host'

from lib.outputManager import OutputManager  # noqa: E402
from lib.updaters.coverUpdater import CoverUpdater  # noqa: E402


class TestCoverUpdater(unittest.TestCase):
    def test_UpdaterInit(self):
        testUpdater = CoverUpdater({'data': 'data'}, 'session')
        self.assertEqual(testUpdater.data, 'data')
        self.assertEqual(testUpdater.session, 'session')
        self.assertEqual(testUpdater.attempts, 0)

    def test_getIdentifier(self):
        testUpdater = CoverUpdater({'data': {}}, 'session')
        testLink = MagicMock()
        testLink.id = 1
        testUpdater.link = testLink
        self.assertEqual(testUpdater.identifier, 1)

    def test_lookupRecord_success(self):
        mockSession = MagicMock()
        mockSession.query().filter().first.return_value = 'existing_link'
        testUpdater = CoverUpdater({'data': {}}, mockSession)
        testUpdater.lookupRecord()
        self.assertEqual(testUpdater.link, 'existing_link')

    @patch.dict('os.environ', {'UPDATE_STREAM': 'test'})
    @patch.object(OutputManager, 'putKinesis')
    def test_lookupRecord_missing(self, mockPut):
        mockSession = MagicMock()
        mockSession.query().filter().first.return_value = None
        testUpdater = CoverUpdater({'data': {}}, mockSession)
        with self.assertRaises(DBError):
            testUpdater.lookupRecord()
            mockPut.assert_called_once_with(
                {'data': {}},
                'test',
                recType='cover',
                attempts=1
            )

    def test_lookupRecord_missing_retries_exceeded(self):
        mockSession = MagicMock()
        mockSession.query().filter().first.return_value = None
        testUpdater = CoverUpdater({'data': {}, 'attempts': 3}, mockSession)
        with self.assertRaises(DBError):
            testUpdater.lookupRecord()

    @patch.dict('os.environ', {'EPUB_STREAM': 'test'})
    @patch.object(OutputManager, 'putKinesis')
    def test_updateRecord(self, mockPut):
        mockLink = MagicMock()
        mockLink.flags = {'temporary': True}
        testUpdater = CoverUpdater({'data': {'storedURL': 's3URL'}}, 'session')
        testUpdater.link = mockLink

        testUpdater.updateRecord()
        self.assertEqual(mockLink.url, 's3URL')
        self.assertEqual(mockLink.flags['temporary'], False)

    @patch('lib.updaters.coverUpdater.datetime')
    def test_setUpdateTime(self, mockUTC):
        testUpdater = CoverUpdater({'data': {}}, 'session')
        testLink = MagicMock()
        testUpdater.link = testLink
        testInstance = MagicMock()
        testLink.instances = [testInstance]
        mockUTC.utcnow.return_value = 1000
        testUpdater.setUpdateTime()
        self.assertEqual(
            testUpdater.link.instances[0].work.date_modified, 1000
        )

    def test_setUpdateTime_noInstance(self):
        testUpdater = CoverUpdater({'data': {}}, 'session')
        testLink = MagicMock()
        testUpdater.link = testLink
        testLink.instances = []
        with self.assertRaises(DBError):
            testUpdater.setUpdateTime()
