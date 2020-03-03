import unittest
from unittest.mock import patch, mock_open, call

from lib.recordFetch import fetchData
from helpers.errorHelpers import OCLCError, DataError


class TestFetcher(unittest.TestCase):
    @patch.dict('os.environ', {'OUTPUT_KINESIS': 'tester', 'OUTPUT_REGION': 'us-test-1'})
    @patch('lib.recordFetch.readFromMARC')
    @patch('lib.recordFetch.lookupRecord')
    def test_basic_fetcher(self, mock_parse, mock_lookup):
        res = fetchData('00000000', 'oclc')
        self.assertTrue(res)

    def test_non_oclc_identifier(self):
        with self.assertRaises(OCLCError):
            fetchData('000000000', 'isbn')
