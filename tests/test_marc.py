import unittest
from unittest.mock import patch, MagicMock, call
from requests.exceptions import ConnectionError

from lib.marcParse import (
    parseMARC,
    transformMARC,
    extractAgentValue,
    extractHoldingsLinks,
    extractSubjects,
    extractSubfieldValue,
    parseHoldingURI
)
from lib.dataModel import WorkRecord, InstanceRecord
from helpers.errorHelpers import DataError


class TestMARC(unittest.TestCase):
    ############
    # Unit Tests
    ############
    @patch('lib.marcParse.transformMARC', side_effect=['test1', None, 'test2'])
    def test_parse_list(self, mock_marc):
        res = parseMARC([1, 2, 3], 'test_rels')
        self.assertEqual(res, ['test1', 'test2'])
    
    @patch('lib.marcParse.extractSubfieldValue')
    @patch('lib.marcParse.extractAgentValue')
    @patch('lib.marcParse.extractHoldingsLinks')
    @patch('lib.marcParse.extractSubjects')
    def test_transform(self, mock_subfield, mock_agent, mock_links, mock_subjects):
        mock_marc = MagicMock()
        
        lang_field = MagicMock()
        mock_eng = MagicMock()
        mock_eng.value = 'English'
        mock_und = MagicMock()
        mock_und.value = 'undefined'
        lang_field.subfield.return_value = [mock_eng, mock_und]

        mockDict = {'546': [lang_field], '856': None}
        def lclgetitem(name):
            return mockDict[name]
        
        mock_marc.__getitem__.side_effect = lclgetitem
        
        testWork = transformMARC(
            ('doab:test', '2019-01-01', mock_marc),
            'test_rels'
        )
        self.assertEqual(testWork.identifiers[0].identifier, 'doab:test')
        self.assertEqual(testWork.instances[0].rights[0].source, 'doab')
        self.assertEqual(testWork.language[0].iso_3, 'eng')
    
    def test_agent_create(self):
        testRec = MagicMock()
        testRec.agents = []

        mock_name = MagicMock()
        mock_name.value = 'Test, Tester'
        mock_role = MagicMock()
        mock_role.value = 'tst'
        
        testData = {
            '100': [{
                'a': [mock_name],
                '4': [mock_role]
            }]
        }

        testRels = {
            'tst': 'testing'
        }

        extractAgentValue(testData, testRec, '100', testRels)
        self.assertEqual(testRec.agents[0].name, 'Test, Tester')
        self.assertEqual(testRec.agents[0].roles[0], 'testing')
    
    @patch('lib.marcParse.parseHoldingURI', side_effect=[
        ('uri1', 'text/html'),
        ('uri2', 'application/pdf')
    ])
    def test_add_links(self, mock_parse):
        testRec = MagicMock()
        testItem = MagicMock()
        
        mock_bad = MagicMock()
        mock_bad.ind1 = 'err'

        mock_html = MagicMock()
        mock_html.ind1 = '4'

        mock_pdf = MagicMock()
        mock_pdf.ind1 = '4'
        mock_url = MagicMock()
        mock_url.value = 'general/url'
        
        mock_note = MagicMock()
        mock_note.value = 'DOAB Note'

        mock_missing = MagicMock()
        mock_missing.ind1 = '4'
        mock_missing.subfield.side_effect = IndexError

        def side_effect(subfield):
            subs = {
                'u': [mock_url],
                'z': [mock_note]
            }
            return subs[subfield]
        mock_pdf.subfield.side_effect = side_effect
        mock_html.subfield.side_effect = side_effect
        
        testHoldings = [
            mock_bad,
            mock_html,
            mock_pdf,
            mock_missing
        ]

        extractHoldingsLinks(testHoldings, testRec, testItem)

        self.assertEqual(2, testItem.addClassItem.call_count)
    
    @patch('lib.marcParse.requests')
    def test_parse_holding_success(self, mock_req):
        mock_redirect = MagicMock()
        mock_redirect.status_code = 302
        mock_redirect.headers = {'Location': 'testURI'}
        mock_head = MagicMock()
        mock_head.headers = {'Content-Type': 'text/testing'}

        mock_req.head.side_effect = [mock_redirect, mock_head]
        
        outURI, contentType = parseHoldingURI('testURI')
        
        mock_req.head.assert_has_calls([
            call('testURI', allow_redirects=False),
            call('testURI', allow_redirects=False)
        ])
        self.assertEqual(outURI, 'testURI')
        self.assertEqual(contentType, 'text/testing')
    
    @patch('lib.marcParse.requests.head', side_effect=ConnectionError)
    def test_parse_holding_error(self, mock_head):
        with self.assertRaises(DataError):
            parseHoldingURI('errorURI')
    
    @patch('lib.marcParse.requests.head')
    def test_parse_holding_no_type(self, mock_head):
        mock_header = MagicMock()
        mock_header.headers = {}
        mock_head.return_value = mock_header
        testURI, contentType = parseHoldingURI('noContentURI')

        self.assertEqual(testURI, 'noContentURI')
        self.assertEqual(contentType, 'text/html')
    
    def test_600_subjects(self):

        testSubj = MagicMock()
        testSubfield = MagicMock()
        testSubfield.value = 'test'
        testSubj.subfield.return_value = [testSubfield]
        testData = {
            '600': [testSubj]
        }

        testRec = MagicMock()

        extractSubjects(testData, testRec, '600')

        testRec.addClassItem.assert_called_once()
    
    def test_610_subjects(self):

        testSubj = MagicMock()
        testSubj.ind2 = '7'
        testSubfield = MagicMock()
        testSubfield.value = 'test'
        testSubj.subfield.return_value = [testSubfield]
        testData = {
            '610': [testSubj]
        }

        testRec = MagicMock()

        extractSubjects(testData, testRec, '610')

        testRec.addClassItem.assert_called_once()
    
    def test_655_subjects(self):

        testSubj = MagicMock()
        testSubfield = MagicMock()
        testSubfield.value = 'test'
        testSubfield.side_effect = IndexError
        testSubj.subfield.side_effect = IndexError
        testData = {
            '655': [testSubj]
        }

        testRec = MagicMock()

        extractSubjects(testData, testRec, '655')

        testRec.addClassItem.assert_called_once()
    
    def test_subfield_general(self):
        recDict = {'other': None, 'array': [], 'str': 'str'}
        def getitem(name):
            return recDict[name]
        def setitem(name, val):
            recDict[name] = val
    
        testRec = MagicMock()
        testRec.__getitem__.side_effect = getitem
        testRec.__setitem__.side_effect = setitem
        testRec.agents = []
        
        mock_field = MagicMock()
        mock_sub = MagicMock()
        mock_sub.value = 'testing'
        mock_field.subfield.return_value = [mock_sub]

        testData = {
            'test': [mock_field]
        }

        extractSubfieldValue(testData, testRec, ('test', 'other', 't'))
        
        mock_field = MagicMock()
        mock_sub = MagicMock()
        mock_sub.value = 'testing'
        mock_field.subfield.return_value = [mock_sub]

        testData = {
            'test': [mock_field]
        }

        extractSubfieldValue(testData, testRec, ('test', 'array', 't'))

        mock_field = MagicMock()
        mock_sub = MagicMock()
        mock_sub.value = 'testing'
        mock_field.subfield.return_value = [mock_sub]

        testData = {
            'test': [mock_field]
        }

        extractSubfieldValue(testData, testRec, ('test', 'str', 't'))

        mock_field = MagicMock()
        mock_field.subfield.side_effect = IndexError

        testData = {
            'test': [mock_field]
        }

        extractSubfieldValue(testData, testRec, ('test', 'err', 'e'))

        mock_field = MagicMock()
        mock_sub = MagicMock()
        mock_sub.value = 'test_agent'
        mock_field.subfield.return_value = [mock_sub]

        testData = {
            'test': [mock_field]
        }

        extractSubfieldValue(testData, testRec, ('test', 'agents', 'a', 'test'))

        mock_field = MagicMock()
        mock_sub = MagicMock()
        mock_sub.value = 'test_id'
        mock_field.subfield.return_value = [mock_sub]

        testData = {
            'test': [mock_field]
        }

        extractSubfieldValue(testData, testRec, ('test', 'identifiers', 'i', 'test'))

        mock_field = MagicMock()
        mock_sub = MagicMock()
        mock_sub.value = 'test_id'
        mock_field.subfield.return_value = [mock_sub]

        testData = {
            'test': [mock_field]
        }

        extractSubfieldValue(testData, testRec, ('test', 'pub_date', 'd'))
        
        self.assertEqual(testRec.agents[0].name, 'test_agent')
        self.assertEqual(testRec['str'], 'str; testing')
        self.assertEqual(testRec['array'], ['testing'])
        self.assertEqual(testRec['other'], 'testing')
        self.assertEqual(2, testRec.addClassItem.call_count)
    
    ###################
    # Functional Tests
    ###################

    def test_transformMARC_5XX_fields(self):
        mockMarc = MagicMock()
        mockMarc.name = 'testing_5XX'
        testRec = (
            1,
            '2019-01-01',
            mockMarc
        )
        
        def mockField(fieldCode):
            mockField = MagicMock()
            mockValue = MagicMock()
            if fieldCode == '505':
                mockValue.value = 'table of contents'
            elif fieldCode == '520':
                mockValue.value = 'summary'
            else:
                mockValue.value = 'test'
            mockField.subfield.return_value = [mockValue]
            return [mockField]

        mockMarc.__getitem__.side_effect = lambda field: mockField(field)

        testWork = transformMARC(testRec, {})
        self.assertIsInstance(testWork, WorkRecord)
        self.assertIsInstance(testWork.instances[0], InstanceRecord)
        self.assertEqual(testWork.instances[0].summary, 'summary')
        self.assertEqual(testWork.instances[0].table_of_contents, 'table of contents')
