from lxml import etree
import unittest
from unittest.mock import MagicMock, Mock, patch

from lib.parsers.parseOCLC import readFromClassify
from lib.dataModel import WorkRecord
from lib.outputManager import OutputManager

class TestOCLCParse(unittest.TestCase):

    @patch.object(OutputManager, 'checkRecentQueries', return_value=False)
    def test_classify_read(self, mockCheck):
        mockXML = Mock()
        work = etree.Element('work',
            title='Test Work',
            editions='1',
            holdings='1',
            eholdings='1',
            owi='1111111',
        )
        work.text = '0000000000'
        mockXML.find = MagicMock(return_value=work)
        mockXML.findall = MagicMock(return_value=[])
        res = readFromClassify(mockXML, 'testUUID')
        self.assertIsInstance(res, WorkRecord)
        mockCheck.assert_called_once_with('lookup/owi/1111111')
