import unittest
from unittest.mock import patch, MagicMock

from lib.marcParse import parseMARC, transformMARC, extractAgentValue, extractHoldingsLinks, extractSubjects, extractSubfieldValue
from helpers.errorHelpers import DataError


class TestMARC(unittest.TestCase):

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
        self.assertEqual(testWork.language[0].iso3, 'eng')
    
    def test_agent_create(self):
        testData = {
            '100': [MagicMock()]
        }
        
        testRec = MagicMock()
        testRec.agents = []

        mock_name = MagicMock()
        mock_name.value = 'Test, Tester'
        mock_role = MagicMock()
        mock_role.value = 'tst'
        
        def side_effect(subfield):
            subs = {
                'a': [mock_name],
                '4': [mock_role]
            }
            return subs[subfield]

        testData['100'][0].subfield.side_effect = side_effect
        testRels = {
            'tst': 'testing'
        }

        extractAgentValue(testData, testRec, '100', testRels)
        self.assertEqual(testRec.agents[0].name, 'Test, Tester')
        self.assertEqual(testRec.agents[0].roles[0], 'testing')
    
    def test_add_links(self):
        testRec = MagicMock()
        testItem = MagicMock()
        
        mock_bad = MagicMock()
        mock_bad.ind1 = 'err'

        mock_pdf = MagicMock()
        mock_pdf.ind1 = '4'
        mock_url = MagicMock()
        mock_url.value = 'general/url'
        mock_note = MagicMock()
        mock_note.value = 'DOAB Note'

        mock_missing = MagicMock()
        mock_missing.ind1 = '4'
        mock_missing.subfield.side_effect = IndexError

        mock_no_note = MagicMock()
        mock_no_note.ind1 = '4'
        

        def side_effect(subfield):
            subs = {
                'u': [mock_url],
                'z': [mock_note]
            }
            return subs[subfield]
        mock_pdf.subfield.side_effect = side_effect

        def side_error(subfield):
            subs = {
                'u': [mock_url]
            }
            if subfield == 'z':
                raise IndexError
            return subs[subfield]
        mock_no_note.subfield.side_effect = side_error
        
        testHoldings = [
            mock_bad,
            mock_pdf,
            mock_missing,
            mock_no_note
        ]

        extractHoldingsLinks(testHoldings, testRec, testItem)

        self.assertEqual(2, testItem.addClassItem.call_count)
    
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



