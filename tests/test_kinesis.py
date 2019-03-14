import unittest
from unittest.mock import patch, mock_open, call
from botocore.stub import Stubber
import botocore
import json
import os
os.environ['OUTPUT_REGION'] = 'us-test-1'

from lib.outputManager import OutputManager
from helpers.errorHelpers import OutputError

class TestKinesis(unittest.TestCase):

    @patch.dict('os.environ', {'OUTPUT_KINESIS': 'tester', 'OUTPUT_SHARD': '0', 'OUTPUT_STAGE': 'test'})
    def test_putRecord(self):
        kinesis = OutputManager()
        stubber = Stubber(kinesis.KINESIS_CLIENT)
        expResp = {
            'ShardId': '1',
            'SequenceNumber': '0'
        }

        record = {
            'type': 'work',
            'method': 'update',
            'data': {'test': 'data'}
        }

        body = json.dumps({
            'status': 200,
            'data': record
        })

        expected_params = {
            'Data': body,
            'StreamName': 'testStream',
            'PartitionKey': '0'
        }

        stubber.add_response('put_record', expResp, expected_params)
        stubber.activate()

        kinesis.putKinesis(record, 'testStream')

    @patch.dict('os.environ', {'OUTPUT_KINESIS': 'tester', 'OUTPUT_SHARD': '0', 'OUTPUT_STAGE': 'test'})
    def test_putRecord_err(self):
        kinesis = OutputManager()
        stubber = Stubber(kinesis.KINESIS_CLIENT)

        record = {'test': 'data'}

        body = json.dumps({
            'status': 200,
            'stage': 'test',
            'data': record
        })

        expected_params = {
            'Data': body,
            'StreamName': 'tester',
            'PartitionKey': '0'
        }

        stubber.add_client_error('put_record', expected_params=expected_params)
        stubber.activate()
        try:
            kinesis.putKinesis(record, 'testStream')
        except OutputError:
            pass
        self.assertRaises(OutputError)
