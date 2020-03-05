import os
import json
import unittest
from unittest.mock import patch, MagicMock

from helpers.errorHelpers import VIAFError
from lib.viaf import VIAFSearch


@patch.dict(os.environ, {'VIAF_API': 'oclcAPI?', 'REDIS_ARN': 'AWSARN'})
class TestVIAFSearch(unittest.TestCase):
    def test_create_search_object(self):
        testInstance = VIAFSearch('Test Name', 'personal')
        self.assertEqual(testInstance.queryName, 'Test Name')
        self.assertEqual(testInstance.viaf_endpoint, 'oclcAPI?')

    @patch('lib.viaf.VIAFSearch.checkCache', return_value=None)
    @patch('lib.viaf.VIAFSearch.searchVIAF')
    @patch('lib.viaf.VIAFSearch.parseVIAF', return_value=True)
    def test_exec_query_hit_oclc(self, mock_parse, mock_search, mock_cache):
        queryTest = VIAFSearch('Test', 'personal')
        response = queryTest.query()
        mock_cache.assert_called_once()
        mock_search.assert_called_once()
        mock_parse.assert_called_once()
        self.assertTrue(response)

    @patch('lib.viaf.VIAFSearch.checkCache', return_value={b'test': b'test'})
    @patch('lib.viaf.VIAFSearch.formatResponse', return_value=True)
    def test_exec_query_hit_cache(self, mock_format, mock_cache):
        queryTest = VIAFSearch('Test', 'personal')
        response = queryTest.query()
        mock_format.assert_called_once()
        mock_cache.assert_called_once()
        self.assertTrue(response)

    @patch('lib.viaf.requests.get')
    def test_viaf_search_success(self, mock_get):
        searchTest = VIAFSearch('Test', 'personal')

        req_mock = MagicMock()
        mock_get.return_value = req_mock
        req_mock.status_code = 200
        req_mock.json.return_value = {'result': 'test'}

        result = searchTest.searchVIAF()
        mock_get.assert_called_once_with('oclcAPI?Test')
        self.assertTrue(result)

    @patch('lib.viaf.requests.get')
    def test_viaf_search_success_url_chars(self, mock_get):
        searchTest = VIAFSearch('Test & Co', 'corporate')

        req_mock = MagicMock()
        mock_get.return_value = req_mock
        req_mock.status_code = 200
        req_mock.json.return_value = {'result': 'test'}

        result = searchTest.searchVIAF()
        mock_get.assert_called_once_with('oclcAPI?Test+%26+Co')
        self.assertTrue(result)

    @patch('lib.viaf.requests.get')
    def test_viaf_search_error(self, mock_get):
        searchTest = VIAFSearch('Test', 'personal')

        req_mock = MagicMock()
        mock_get.return_value = req_mock
        req_mock.status_code = 500
        try:
            searchTest.searchVIAF()
        except VIAFError:
            pass
        mock_get.assert_called_once()
        self.assertRaises(VIAFError)

    @patch('lib.viaf.VIAFSearch.setCache')
    @patch('lib.viaf.VIAFSearch.formatResponse', return_value=True)
    def test_viaf_parse_response(self, mock_format, mock_cache):
        parseTest = VIAFSearch('Test', 'personal')
        mock_json = [
            {
                'displayForm': 'Test Co.',
                'viafid': '987654321',
                'nametype': 'corporate'
            }, {
                'displayForm': 'Test',
                'viafid': '123456789',
                'nametype': 'personal'
            }
        ]

        parsed = parseTest.parseVIAF(mock_json)
        mock_cache.assert_called_once()
        mock_format.assert_called_once()
        self.assertTrue(parsed)

    @patch('lib.viaf.VIAFSearch.setCache')
    @patch('lib.viaf.VIAFSearch.formatResponse', return_value=False)
    def test_viaf_parse_response_wrong_type(self, mock_format, mock_cache):
        parseTest = VIAFSearch('Test', 'personal')
        mock_json = [
            {
                'displayForm': 'Test Co.',
                'viafid': '987654321',
                'nametype': 'corporate'
            }
        ]

        parsed = parseTest.parseVIAF(mock_json)
        mock_cache.assert_not_called()
        mock_format.assert_called_once()
        self.assertFalse(parsed)

    @patch('lib.viaf.VIAFSearch.formatResponse', return_value=True)
    def test_viaf_parse_none(self, mock_format):
        parseTest = VIAFSearch('Test', 'personal')
        parsed = parseTest.parseVIAF(None)
        mock_format.assert_called_once()
        self.assertTrue(parsed)

    def test_check_cache_found(self):
        cacheTest = VIAFSearch('Test', 'personal')
        mock_redis = MagicMock()
        mock_redis.hgetall.return_value = {'test': 'test'}
        cacheTest.redis = mock_redis

        cacheOut = cacheTest.checkCache()
        self.assertEqual(cacheOut['test'], 'test')

    def test_check_cache_not_found(self):
        cacheTest = VIAFSearch('Test', 'personal')
        mock_redis = MagicMock()
        mock_redis.hgetall.return_value = {}
        cacheTest.redis = mock_redis

        cacheOut = cacheTest.checkCache()
        self.assertEqual(cacheOut, None)

    def test_set_cache_value(self):
        cacheTest = VIAFSearch('Test', 'personal')
        mock_redis = MagicMock()
        cacheTest.redis = mock_redis

        mock_viaf = {
            'name': 'Test',
            'viaf': '123456789',
            'lcnaf': None
        }

        cacheTest.setCache(mock_viaf)
        mock_redis.hmset.assert_called_once_with(
            'personal/Test',
            {
                'name': 'Test',
                'viaf': '123456789'
            }
        )

    def test_format_response(self):
        testResp = VIAFSearch.formatResponse(200, {'test': 'test'})
        self.assertEqual(testResp['statusCode'], 200)
        self.assertEqual(json.loads(testResp['body'])['test'], 'test')

    def test_raise_on_incorrect_type(self):
        with self.assertRaises(VIAFError):
            VIAFSearch('test', 'test')
