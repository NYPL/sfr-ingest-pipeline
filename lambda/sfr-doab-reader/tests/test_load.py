import unittest
from unittest.mock import patch, MagicMock
import os
import json
from datetime import datetime

from lib.load import Loaders
from helpers.errorHelpers import OAIFeedError, DataError


class TestLoaders(unittest.TestCase):

    def setUp(self):
        os.environ['DOAB_OAI_ROOT'] = 'test_root_url'
        os.environ['LOAD_DAYS_AGO'] = '0'
        os.environ['MARC_RELATORS'] = 'test_loc_url'
    
    def tearDown(self):
        del os.environ['DOAB_OAI_ROOT']
        del os.environ['LOAD_DAYS_AGO']
        del os.environ['MARC_RELATORS']

    def test_loader_init(self):
        tdTest = datetime(2019, 1, 1)
        with patch('lib.load.datetime') as mock_date:
            mock_date.now.return_value = datetime(2019, 1, 1)
            tester = Loaders()
            self.assertEqual(tester.doab_root, 'test_root_url')
            self.assertEqual(tester.load_since, tdTest)
    
    def test_load_oai(self):
        with patch('lib.load.requests') as mock_request:
            mockResp = MagicMock()
            mockResp.status_code = 200
            mockResp.content = 'test_content'
            mock_request.get.return_value = mockResp

            tester = Loaders()

            res = tester.loadOAIFeed()
            mock_request.get.assert_called_once()
            self.assertEqual(res, 'test_content')
    
    def test_load_oai_resumption(self):
        with patch('lib.load.requests') as mock_request:
            mockResp = MagicMock()
            mockResp.status_code = 200
            mockResp.content = 'test_content'
            mock_request.get.return_value = mockResp

            tester = Loaders()

            res = tester.loadOAIFeed('token')
            mock_request.get.assert_called_once()
            self.assertEqual(res, 'test_content')
    
    def test_oai_error(self):
        with patch('lib.load.requests') as mock_request:
            mockResp = MagicMock()
            mockResp.status_code = 500
            mockResp.content = 'test_content'
            mock_request.get.return_value = mockResp
            tester = Loaders()
            with self.assertRaises(OAIFeedError):
                tester.loadOAIFeed()
    
    def test_oai_single(self):
        with patch('lib.load.requests') as mock_request:
            mockResp = MagicMock()
            mockResp.status_code = 200
            mockResp.content = 'test_single'
            mock_request.get.return_value = mockResp

            tester = Loaders()

            res = tester.loadOAIRecord('test_url')
            mock_request.get.assert_called_once()
            self.assertEqual(res, 'test_single')
    
    def test_single_error(self):
        with patch('lib.load.requests') as mock_request:
            mockResp = MagicMock()
            mockResp.status_code = 500
            mockResp.content = 'test_single'
            mock_request.get.return_value = mockResp
            tester = Loaders()
            with self.assertRaises(OAIFeedError):
                tester.loadOAIRecord('test_url')
    
    def test_load_relators(self):
        with patch('lib.load.requests') as mock_request:
            mockResp = MagicMock()
            mockResp.status_code = 200
            mockResp.content = json.dumps([
                {
                    '@id': 'some/authority/tst',
                    'http://www.loc.gov/mads/rdf/v1#authoritativeLabel': [{
                        '@value': 'test'
                    }]
                },{
                    '@id': 'some/authority/deprecated'
                }
            ])
            mock_request.get.return_value = mockResp
            tester = Loaders()
            terms = tester.loadMARCRelators()
            self.assertEqual(terms['tst'], 'test')

    def test_relator_error(self):
        with patch('lib.load.requests') as mock_request:
            mockResp = MagicMock()
            mockResp.status_code = 500
            mockResp.content = 'relator_json'
            mock_request.get.return_value = mockResp
            tester = Loaders()
            with self.assertRaises(DataError):
                tester.loadMARCRelators()
