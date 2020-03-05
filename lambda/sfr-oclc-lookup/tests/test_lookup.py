import unittest
from unittest.mock import patch, mock_open, call
from collections import namedtuple
from lxml import etree
from requests.exceptions import ConnectionError

from lib.readers.oclcLookup import lookupRecord, parseMARC, catalogLookup, createURL

from helpers.errorHelpers import OCLCError, DataError

class TestLookup(unittest.TestCase):

    @patch('lib.readers.oclcLookup.createURL')
    @patch('lib.readers.oclcLookup.catalogLookup')
    @patch('lib.readers.oclcLookup.parseMARC', return_value=True)
    def test_look_manager(self, mock_url, mock_catalog, mock_parse):
        res = lookupRecord('00000000')
        mock_url.assert_called_once()
        mock_catalog.assert_called_once()
        mock_parse.assert_called_once()
        self.assertTrue(res)

    @patch('lib.readers.oclcLookup.etree.fromstring')
    @patch('lib.readers.oclcLookup.marcalyx.Record', return_value=True)
    def test_marc_parse(self, mock_string, mock_marc):
        res = parseMARC('00000000')
        mock_string.assert_called_once()
        mock_marc.assert_called_once()
        self.assertTrue(res)

    @patch('lib.readers.oclcLookup.etree.fromstring', side_effect=OCLCError('error'))
    @patch('lib.readers.oclcLookup.marcalyx.Record', return_value=True)
    def test_marc_raise_xml(self, mock_marc, mock_string):

        try:
            res = parseMARC('00000000')
        except OCLCError:
            pass

        mock_marc.assert_not_called()
        self.assertRaises(OCLCError)

    @patch('lib.readers.oclcLookup.etree.fromstring')
    @patch('lib.readers.oclcLookup.marcalyx.Record', side_effect=OCLCError('error'))
    def test_marc_raise_marcalyx(self, mock_marc, mock_string):

        try:
            res = parseMARC('00000000')
        except OCLCError:
            pass

        mock_string.assert_called_once()
        mock_marc.assert_called_once()
        self.assertRaises(OCLCError)

    reqReturn = namedtuple('Return', ['status_code', 'text'])
    reqReturn.status_code=200
    reqReturn.text = True
    @patch('lib.readers.oclcLookup.requests.get', return_value=reqReturn)
    def test_requests_success(self, mock_request):
        res = catalogLookup('url')
        self.assertTrue(res)

    failReturn = namedtuple('Return', ['status_code', 'text'])
    failReturn.status_code=500
    failReturn.body='error'
    @patch('lib.readers.oclcLookup.requests.get', return_value=failReturn)
    def test_requests_err(self, mock_request):
        try:
            res = catalogLookup('url')
        except OCLCError:
            pass
        self.assertRaises(OCLCError)
    
    reqReturn = namedtuple('Return', ['status_code', 'text'])
    reqReturn.status_code=200
    reqReturn.text = True
    @patch('lib.readers.oclcLookup.requests.get', side_effect=[ConnectionError, reqReturn])
    def test_requests_retry_success(self, mock_request):
        res = catalogLookup('url')
        self.assertTrue(res)

    @patch.dict('os.environ', {'OCLC_KEY': '000'})
    def test_create_url(self):
        res = createURL('00000000')
        self.assertEqual(res, 'http://www.worldcat.org/webservices/catalog/content/00000000?wskey=000')
