from lxml import etree
import unittest
from unittest.mock import MagicMock, Mock, patch, DEFAULT

from lib.parsers.parseOCLC import extractHoldingsLinks 
from lib.parsers.parse856Holding import HoldingParser
from lib.dataModel import WorkRecord
from helpers.errorHelpers import HoldingError

class TestOCLCParse(unittest.TestCase):
    @patch.multiple(
        HoldingParser,
        parseField=DEFAULT,
        extractBookLinks=DEFAULT
    )
    def test_holdings_extraction(self, parseField, extractBookLinks):
        mock_instance = MagicMock()
        mock_holding = MagicMock()
        extractHoldingsLinks([mock_holding], mock_instance)
        parseField.assert_called_once()
        extractBookLinks.assert_called_once()
    
    @patch.multiple(
        HoldingParser,
        parseField=DEFAULT,
        extractBookLinks=DEFAULT
    )
    def test_holdings_raise_error(self, parseField, extractBookLinks):
        parseField.side_effect = HoldingError('Test Error')
        mock_holding = MagicMock()
        mock_instance = MagicMock()
        extractHoldingsLinks([mock_holding], mock_instance)
        parseField.assert_called_once()
        extractBookLinks.assert_not_called()
