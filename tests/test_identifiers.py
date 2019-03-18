import unittest
from unittest.mock import patch, MagicMock
from collections import defaultdict, namedtuple

from helpers.errorHelpers import DataError
from model.identifiers import (
    Identifier,
    DOAB,
    Hathi,
    Gutenberg,
    OCLC,
    LCCN,
    ISBN,
    OWI,
    ISSN,
    LCC,
    DDC,
    GENERIC
)

TestIdentifer = namedtuple('TestIdentifier', ['id', 'value', 'identifier_id'])


class TestIdentifiers(unittest.TestCase):
    
    def test_found_single_identifier(self):
        mock_session = MagicMock()
        mock_session.query().join().filter().all.return_value = [(1,)]
        mock_instance = MagicMock()
        ids = [
            {
                'identifier': '1234567890',
                'type': 'isbn'
            }
        ]

        result = Identifier.getByIdentifier(mock_instance, mock_session, ids)
        self.assertEqual(result, 1)
    
    def test_new_identifier(self):
        mock_session = MagicMock()
        mock_session.query().join().filter().all.return_value = []
        mock_instance = MagicMock()
        ids = [
            {
                'identifier': '1234567890',
                'type': 'isbn'
            }
        ]

        result = Identifier.getByIdentifier(mock_instance, mock_session, ids)
        self.assertEqual(result, None)
    
    def test_generic_identifier(self):
        mock_session = MagicMock()
        mock_session.query().join().filter().all.return_value = [(1,)]
        mock_instance = MagicMock()
        ids = [
            {
                'identifier': '000000000',
                'type': 'isbn'
            }
        ]

        result = Identifier.getByIdentifier(mock_instance, mock_session, ids)
        self.assertEqual(result, None)
    
    def test_skip_identifier(self):
        mock_session = MagicMock()
        mock_session.query().join().filter().all.return_value = [(1,)]
        mock_instance = MagicMock()
        ids = [
            {
                'identifier': '1234567890',
                'type': 'isbn'
            },{
                'identifier': '999.99',
                'type': 'ddc'
            }
        ]

        result = Identifier.getByIdentifier(mock_instance, mock_session, ids)
        self.assertEqual(result, 1)
    
    @patch('model.identifiers.Equivalent')
    def test_multi_identifier(self, mock_equivalent):
        mock_session = MagicMock()
        mock_session.query().join().filter().all.side_effect = [
            [(1,), (2,)],
            [(1,)]
        ]
        mock_instance = MagicMock()
        mock_instance.__tablename__ = 'test_table'
        ids = [
            {
                'identifier': '1234567890',
                'type': 'isbn'
            },{
                'identifier': '0987654321',
                'type': 'oclc'
            }
        ]

        result = Identifier.getByIdentifier(mock_instance, mock_session, ids)
        mock_equivalent.addEquivalencies.assert_called_once()
        self.assertEqual(result, 1)

    def test_clean_id(self):
        clean = Identifier._cleanIdentifier('id (test)')
        self.assertEqual(clean, 'id')
    
    def test_clean_error(self):
        with self.assertRaises(DataError):
            Identifier._cleanIdentifier('NAN')
    
    def test_top_match(self):
        testMatches = [
            (1, 2),
            (2, 1)
        ]
        testTop = Identifier._getTopMatch(testMatches)
        self.assertEqual(testTop, 1)
    
    def test_top_match_equiv(self):
        testMatches = [
            (1, 1),
            (2, 1)
        ]
        testTop = Identifier._getTopMatch(testMatches)
        self.assertEqual(testTop, None)
    
    def test_top_match_single(self):
        testMatches = [
            (1, 1)
        ]
        testTop = Identifier._getTopMatch(testMatches)
        self.assertEqual(testTop, 1)
    
    def test_assign_recs(self):
        testRecs = [
            (1,),
            (2,),
            (1,)
        ]
        testMatches = defaultdict(int)
        Identifier._assignRecs(testRecs, testMatches)
        self.assertEqual(testMatches[1], 2)
        self.assertEqual(testMatches[2], 1)
    
    def test_order_identifiers(self):
        testIDs = [
            {
                'type': 'isbn',
                'value': 'first'
            },{
                'type': 'gutenberg',
                'value': 'last'
            },{
                'type': 'owi',
                'value': 'middle'
            }
        ]
        sortedIDs = Identifier._orderIdentifiers(testIDs)
        self.assertEqual(sortedIDs[0]['value'], 'first')
        self.assertEqual(sortedIDs[1]['value'], 'middle')
        self.assertEqual(sortedIDs[2]['value'], 'last')