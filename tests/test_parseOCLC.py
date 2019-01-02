from lxml import etree
import unittest
from unittest.mock import MagicMock, Mock

from lib.parsers.parseOCLC import readFromClassify
from lib.dataModel import WorkRecord

class TestOCLCParse(unittest.TestCase):

    def test_classify_read(self):
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
        res = readFromClassify(mockXML)
        self.assertIsInstance(res, WorkRecord)
