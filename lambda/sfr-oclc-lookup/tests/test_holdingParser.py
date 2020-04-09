import unittest
from unittest.mock import call, DEFAULT, MagicMock, patch

from lib.parsers.parse856Holding import HoldingParser
from helpers.errorHelpers import HoldingError


class TestHoldingParse(unittest.TestCase):
    def test_create_class(self):
        testInst = HoldingParser('mock856', 'mockInstance')
        self.assertIsInstance(testInst, HoldingParser)
        self.assertEqual(testInst.field, 'mock856')
        self.assertEqual(testInst.instance, 'mockInstance')
        self.assertEqual(testInst.source, 'unknown')
    
    @patch.object(HoldingParser, 'loadURIid')
    def test_parseField_success(self, mockURILoad):
        mockField = MagicMock()
        mockField.ind1 = '4'
        
        mockSubU = MagicMock()
        mockSubU.value = 'testURI'

        mockField.subfield.return_value = [mockSubU]

        testInst = HoldingParser(mockField, 'mockInstance')

        testInst.parseField()
        self.assertEqual(testInst.uri, 'testURI')
        mockURILoad.assert_called_once()
    
    def test_parseField_wrong_ind1(self):
        mockField = MagicMock()
        mockField.ind1 = '1'

        testInst = HoldingParser(mockField, 'mockInstance')
        with self.assertRaises(HoldingError):
            testInst.parseField()

    def test_parseField_missing_u_subfield(self):
        mockField = MagicMock()
        mockField.ind1 = '4'
        mockField.subfield.side_effect = IndexError

        testInst = HoldingParser(mockField, 'mockInstance')
        with self.assertRaises(HoldingError):
            testInst.parseField()

    def test_loadURIid_found_match(self):
        testInst = HoldingParser('mock856', 'mockInstance')
        testInst.uri = 'http://www.test.org/123-abc.test'
        testInst.loadURIid()
        self.assertEqual(testInst.identifier, '123-abc')

    def test_loadURIid_missing_match_group(self):
        testInst = HoldingParser('mock856', 'mockInstance')
        testInst.uri = 'test.org'
        testInst.loadURIid()
        self.assertEqual(testInst.identifier, 'test.org')

    @patch.multiple(HoldingParser, matchEbook=DEFAULT, matchIdentifier=DEFAULT)
    def test_extractBookLinks_ebookMatch(self, matchEbook, matchIdentifier):
        matchEbook.return_value = True
        testInst = HoldingParser('mock856', 'mockInstance')
        testInst.extractBookLinks()
        matchEbook.assert_called_once()
        matchIdentifier.assert_not_called()

    @patch.multiple(HoldingParser, matchEbook=DEFAULT, matchIdentifier=DEFAULT)
    def test_extractBookLinks_idMatch(self, matchEbook, matchIdentifier):
        matchEbook.return_value = False
        matchIdentifier.return_value = True
        testInst = HoldingParser('mock856', 'mockInstance')
        testInst.extractBookLinks()
        matchEbook.assert_called_once()
        matchIdentifier.assert_called_once()

    @patch.multiple(
        HoldingParser,
        matchEbook=DEFAULT,
        matchIdentifier=DEFAULT,
        createLink=DEFAULT
    )
    def test_extractBookLinks_no_Match(
        self, matchEbook, matchIdentifier, createLink
    ):
        matchEbook.return_value = False
        matchIdentifier.return_value = False 
        createLink.return_value = 'testLink'
        mockInstance = MagicMock()
        mockInstance.links = []
        testInst = HoldingParser('mock856', mockInstance)
        testInst.uri = 'testURI'
        testInst.extractBookLinks()
        matchEbook.assert_called_once()
        matchIdentifier.assert_called_once()
        createLink.assert_called_once_with('testURI', 'text/html')
        self.assertEqual(testInst.instance.links[0], 'testLink')

    @patch.multiple(
        HoldingParser, checkIAStatus=DEFAULT, parseHathiLink=DEFAULT
    )
    def test_matchEbook_generic(self, checkIAStatus, parseHathiLink):
        mockInstance = MagicMock()
        testInst = HoldingParser('856Field', mockInstance)
        testInst.uri = 'www.test.org/test123.epub'
        testInst.matchEbook()
        checkIAStatus.assert_not_called()
        parseHathiLink.assert_not_called()
        mockInstance.addFormat.assert_not_called()

    @patch.multiple(
        HoldingParser, checkIAStatus=DEFAULT, parseHathiLink=DEFAULT
    )
    def test_matchEbook_gutenberg(self, checkIAStatus, parseHathiLink):
        mockInstance = MagicMock()
        testInst = HoldingParser('856Field', mockInstance)
        testInst.uri = 'gutenberg.org/ebooks/123.epub.images'
        testInst.identifier = 1
        testInst.matchEbook()
        checkIAStatus.assert_not_called()
        parseHathiLink.assert_not_called()
        mockInstance.addFormat.assert_called_once()
    
    @patch.object(HoldingParser, 'checkIAStatus')
    def test_matchEBook_ia_success(self, mockIACheck):
        mockIACheck.return_value = True
        testInst = HoldingParser('856Field', 'mockInstance')
        testInst.uri = 'archive.org/details/testwork00'
        self.assertEqual(testInst.matchEbook(), None)
        mockIACheck.assert_called_once()

    @patch.object(HoldingParser, 'parseHathiLink')
    def test_matchEBook_hathi_success(self, mockParseHathi):
        mockParseHathi.return_value = True
        testInst = HoldingParser('856Field', 'mockInstance')
        testInst.uri = 'catalog.hathitrust.org/api/volumes/abc/n123456789.html'
        self.assertEqual(testInst.matchEbook(), None)
        mockParseHathi.assert_called_once()

    def test_matchIdentifier(self):
        mockInstance = MagicMock()
        testInst = HoldingParser('856Field', mockInstance)
        testInst.uri = 'test.org/oclc/123465'
        self.assertTrue(testInst.matchIdentifier())
        mockInstance.addIdentifier.assert_called_once_with(
            type='oclc', identifier='123465', weight=0.8
        )

    @patch('lib.parsers.parse856Holding.requests')
    def test_checkIAStatus_not_restricted(self, mockReq):
        testInst = HoldingParser('mock856', 'mockInstance')
        testInst.uri = 'archive.org/detail/testwork00'

        mockResp = MagicMock()
        mockResp.status_code = 200
        mockResp.json.return_value = {
            'metadata': {
                'access-restricted-item': False
            }
        }
        mockReq.get.return_value = mockResp
        self.assertFalse(testInst.checkIAStatus())

    @patch('lib.parsers.parse856Holding.requests')
    def test_checkIAStatus_restricted(self, mockReq):
        testInst = HoldingParser('mock856', 'mockInstance')
        testInst.uri = 'archive.org/detail/testwork00'

        mockResp = MagicMock()
        mockResp.status_code = 200
        mockResp.json.return_value = {
            'metadata': {
                'access-restricted-item': True
            }
        }
        mockReq.get.return_value = mockResp
        self.assertTrue(testInst.checkIAStatus())

    @patch.object(HoldingParser, 'loadCatalogLinks')
    def test_parseHathiLink(self, mockLoad):
        testInst = HoldingParser('mock856', 'mockInstance')
        testInst.uri = 'catalog.hathitrust.org'
        testInst.parseHathiLink()
        mockLoad.assert_called_once()

    @patch.object(HoldingParser, 'loadCatalogLinks')
    def test_parseHathiLink_skip(self, mockLoad):
        testInst = HoldingParser('mock856', 'mockInstance')
        testInst.uri = 'babel.hathitrust.org'
        testInst.parseHathiLink()
        mockLoad.assert_not_called()

    @patch.multiple(
        HoldingParser, fetchHathiItems=DEFAULT, startHathiMultiprocess=DEFAULT
    )
    def test_loadCatalogLinks_match_hathiID(
        self, fetchHathiItems, startHathiMultiprocess
    ):
        testInst = HoldingParser('mock856', 'mockInstance')
        testInst.uri = 'catalog.hathitrust.org/volumes/oclc/0123456.html'
        fetchHathiItems.return_value = ['item1', 'item2', 'item3']
        testInst.loadCatalogLinks()
        fetchHathiItems.assert_called_once()
        startHathiMultiprocess.assert_called_once_with([
            'item1', 'item2', 'item3'
        ])

    @patch('lib.parsers.parse856Holding.requests')
    def test_fetchHathiItems(self, mockReq):
        mockResp = MagicMock()
        mockResp.status_code = 200
        mockResp.json.return_value = {'items': 'itemList'}
        mockReq.get.return_value = mockResp

        testInst = HoldingParser('mock856', 'mockInstance')
        testItems = testInst.fetchHathiItems('test.132456')
        self.assertEqual(testItems, 'itemList') 

    def test_getNewItemLinks_not_pd(self):
        testItem = {
            'rightsCode': 'ic-world'
        }
        testInst = HoldingParser('mock856', 'mockInstance')
        self.assertEqual(testInst.getNewItemLinks(testItem), None)
    
    @patch('lib.parsers.parse856Holding.requests')
    @patch.object(HoldingParser, 'createLink')
    def test_getNewItemLinks_pd(self, mockCreate, mockReq):
        testItem = {
            'rightsCode': 'pd',
            'itemURL': 'hathitrust.org/302-redirect'
        }

        mockResp = MagicMock()
        mockResp.headers = {
            'Location': 'https://hathitrust.org/test?id=test.123465' 
        }
        mockReq.head.return_value = mockResp

        mockInstance = MagicMock()

        testInst = HoldingParser('mock856', mockInstance)
        testInst.source = 'hathitrust'
        testInst.identifier = '123465'

        outItem = testInst.getNewItemLinks(testItem)
        self.assertEqual(outItem['source'], 'hathitrust')
        self.assertEqual(len(outItem['links']), 2)
        mockCreate.assert_has_calls([
            call(
                'hathitrust.org/test?id=test.123465',
                'text/html',
                local=False,
                download=False,
                images=True,
                ebook=False
            ),
            call(
                'babel.hathitrust.org/cgi/imgsrv/download/pdf?id=test.123465',
                'application/pdf',
                local=False,
                download=True,
                images=True,
                ebook=False
            )
        ])

    def test_startHathiMultiprocess(self):
        def fakeProcess(items, conn):
            for i in items:
                conn.send(i)
            conn.send('DONE')
            conn.close()
        
        with patch.object(HoldingParser, 'processHathiChunk', wraps=fakeProcess) as mockChunk:
            mockInstance = MagicMock()
            testInst = HoldingParser('mock856', mockInstance)
            testInst.startHathiMultiprocess([{'test': 1}, {'test': 2}])

            mockInstance.addFormat.assert_has_calls([call(test=1), call(test=2)])

    def test_startHathiMultiprocess_raiseEOF(self):
        def fakeProcess(items, conn):
            for i in items:
                conn.send(i)
            conn.close()
        
        with patch.object(HoldingParser, 'processHathiChunk', wraps=fakeProcess) as mockChunk:
            mockInstance = MagicMock()
            testInst = HoldingParser('mock856', mockInstance)
            testInst.startHathiMultiprocess([{'test': 1}, {'test': 2}])

            mockInstance.addFormat.assert_has_calls([call(test=1), call(test=2)])

    @patch.object(HoldingParser, 'getNewItemLinks')
    def test_processHathiChunk(self, mockGetNew):
        testInst = HoldingParser('mock856', 'mockInstance')
        mockGetNew.side_effect = ['item1', None, 'item2']
        mockConn = MagicMock()

        testInst.processHathiChunk([1, 2, 3], mockConn)

        mockGetNew.assert_has_calls([call(1), call(2), call(3)])
        mockConn.send.assert_has_calls([
            call('item1'), call('item2'), call('DONE')]
        )
        mockConn.close.assert_called_once()
