import unittest
from unittest.mock import patch, mock_open, call

import os
os.environ['OUTPUT_REGION'] = 'us-test-1'

from lib.enhancer import enhanceRecord, mergeData
from helpers.errorHelpers import OCLCError
from lib.dataModel import WorkRecord

class TestEnhancer(unittest.TestCase):

    @patch('lib.enhancer.classifyRecord', return_value=(True, True))
    @patch('lib.enhancer.readFromClassify')
    @patch('lib.enhancer.mergeData')
    @patch('lib.enhancer.KinesisOutput.putRecord')
    def test_basic_enhancer(self, mock_classify, mock_read, mock_merge, mock_put):
        testRec = {
            'source': 'test',
            'recordID': 1,
            'data': 'some data'
        }

        res = enhanceRecord(testRec)
        self.assertTrue(res)

    def test_basic_enhancer_missing_field(self):
        testRec = {
            'source': 'test',
            'recordID': 1
        }

        res = enhanceRecord(testRec)
        self.assertFalse(res)

    @patch('lib.enhancer.classifyRecord', return_value=(True, True), side_effect=OCLCError('testing'))
    def test_enhancer_err(self, mock_classify):
        testRec = {
            'source': 'test',
            'recordID': 1,
            'data': 'some data'
        }

        res = enhanceRecord(testRec)
        self.assertFalse(res)
        self.assertRaises(OCLCError)

    @patch('lib.enhancer.Agent.checkForMatches', return_value=['agent', 'author2'])
    def test_merge(self, mock_matches):
        source = {
            'title': 'Source Test',
            'altTitle': ['Source Alt'],
            'instances': ['instance'],
            'agents': ['agent'],
            'subjects': ['subject'],
            'measurements': ['measurement']
        }

        oclcSource = WorkRecord.createFromDict(**{
            'workTitle': 'OCLC Title',
            'altTitles': ['OCLC Alt'],
            'editions': ['instance2'],
            'authors': ['author2'],
            'subjects': ['subject2'],
            'measurements': ['mesurement2']
        })

        data = mergeData(source, oclcSource)
        self.assertEqual(data['title'], 'OCLC Title')
        self.assertEqual(data['agents'], ['agent', 'author2'])
