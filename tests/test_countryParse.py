import unittest
from unittest.mock import patch, mock_open

from lib.countryParser import loadCountryCodes
from helpers.errorHelpers import ProcessingError


class TestCountry(unittest.TestCase):

    def test_country_load(self):
        testData = (
            '<codelist xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="info:lc/xmlns/codelist-v1" version="1.0" xsi:schemaLocation="info:lc/xmlns/codelist-v1 http://www.loc.gov/standards/codelists/codelist.xsd">'
            '<codelistId>marccountry</codelistId>'
            '<title>MARC Code List for Countries</title>'
            '<countries>'
            '<country>'
            '<uri>info:lc/vocabulary/countries/af</uri>'
            '<name authorized="yes">Afghanistan</name>'
            '<code>af</code>'
            '<region>Asia</region>'
            '</country>'
            '</countries>'
            '</codelist>'
        )
        mOpen = mock_open(read_data=testData)
        mOpen.return_value.__iter__ = lambda self: self
        mOpen.return_value.__next__ = lambda self: next(iter(self.readline, ''))
        with patch('lib.countryParser.open', mOpen, create=True):
            countryList = loadCountryCodes()
            self.assertEqual(countryList['af'], 'Afghanistan')

    @patch('lib.countryParser.open', side_effect=FileNotFoundError)
    def test_country_marc_missing(self, mock_parser_open):
        with self.assertRaises(ProcessingError):
            loadCountryCodes()
