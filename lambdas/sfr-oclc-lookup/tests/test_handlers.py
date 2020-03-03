import json
import unittest
from unittest.mock import patch, mock_open, call

# Set this variable here as it gets checked at loadtime
import os
os.environ['OUTPUT_REGION'] = 'us-test-1'

from service import handler
from helpers.errorHelpers import NoRecordsReceived, OCLCError, DataError
from lib.outPutManager import OutputManager


class TestHandler(unittest.TestCase):
    @patch('service.fetchData', return_value='oclcResponse')
    @patch.object(OutputManager, 'formatResponse', return_value='outObject')
    def test_handler_clean(self, mockResponse, mockFetch):
        testRec = {
            'queryStringParameters': {
                'identifier': '000000000',
                'type': 'oclc'
            }
        }
        resp = handler(testRec, None)
        self.assertEqual(resp, 'outObject')
        mockFetch.assert_called_once_with('000000000', 'oclc')
        mockResponse.assert_called_once_with(200, 'oclcResponse')

    @patch.object(OutputManager, 'formatResponse', return_value='outObject')
    def test_handler_error_bad_parameters(self, mockResponse):
        testRec = {
            'queryStringParameters': {
                'identifier': '000000000',
            }
        }
        resp = handler(testRec, None)
        self.assertEqual(resp, 'outObject')
        mockResponse.assert_called_once_with(
            400,
            {'message': 'GET query must include identifier and type'}
        )

    @patch('service.fetchData', side_effect=OCLCError('Test Error'))
    @patch.object(OutputManager, 'formatResponse', return_value='outObject')
    def test_handler_internal_error(self, mockResponse, mockFetch):
        testRec = {
            'queryStringParameters': {
                'identifier': '000000000',
                'type': 'oclc'
            }
        }
        resp = handler(testRec, None)
        self.assertEqual(resp, 'outObject')
        mockFetch.assert_called_once_with('000000000', 'oclc')
        mockResponse.assert_called_once_with(500, {'message': 'Test Error'})
