import unittest
from unittest.mock import patch, DEFAULT

from lib.hathiCover import HathiPage


class TestHathiPage(unittest.TestCase):
    @patch.multiple(
        HathiPage,
        getPageNo=DEFAULT,
        parseFlags=DEFAULT,
        setScore=DEFAULT
    )
    def test_HathiPage_init(self, getPageNo, parseFlags, setScore):
        getPageNo.return_value = 1
        parseFlags.return_value = {'testing': True}
        setScore.return_value = 10

        testPage = HathiPage('data')
        self.assertEqual(testPage.pageData, 'data')
        self.assertEqual(testPage.page, 1)
        self.assertTrue(testPage.flags['testing'])
        self.assertEqual(testPage.score, 10)

    @patch.multiple(HathiPage, parseFlags=DEFAULT, setScore=DEFAULT)
    def test_HathiPage_getPageNo(self, parseFlags, setScore):
        testPage = HathiPage({'ORDER': 3})
        self.assertEqual(testPage.page, 3)

    @patch.multiple(HathiPage, getPageNo=DEFAULT, setScore=DEFAULT)
    def test_HathiPage_parseFlags(self, getPageNo, setScore):
        testPage = HathiPage({'LABEL': 'TITLE, IMAGE_ON_PAGE, TEST'})
        self.assertEqual(
            testPage.flags,
            set(['TITLE', 'IMAGE_ON_PAGE', 'TEST'])
        )

    @patch.multiple(HathiPage, getPageNo=DEFAULT, parseFlags=DEFAULT)
    def test_HathiPage_setScore(self, getPageNo, parseFlags):
        parseFlags.return_value = set(['TITLE', 'FRONT_COVER'])
        testPage = HathiPage('data')
        self.assertEqual(testPage.score, 2)
