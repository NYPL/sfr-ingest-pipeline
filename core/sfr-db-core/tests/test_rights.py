import unittest
from unittest.mock import patch, MagicMock
from collections import namedtuple

from sfrCore.model import Rights

RightsTup = namedtuple('TestRights',
    ['id', 'source', 'license', 'rights_statement', 'rights_reason', 'dates']
)


class TestRights(unittest.TestCase):

    @patch.object(Rights, 'lookupRights', return_value=None)
    @patch.object(Rights, 'insert', return_value=True)
    def test_check_new(self, mock_insert, mock_lookup):
        res = Rights.updateOrInsert(
            'session',
            {'license': 'rghts'},
            'Rights',
            1
        )
        mock_lookup.expect_to_be_called()
        self.assertTrue(res)

    def test_check_existing(self):
        mock_rights = MagicMock()
        mock_rights.value = 'testRights'
        with patch.object(Rights, 'lookupRights', return_value=mock_rights) as mock_lookup:
            res = Rights.updateOrInsert(
                'session',
                {'license': 'new_uri'},
                'Date',
                1
            )
            mock_lookup.expect_to_be_called()
            mock_rights.update.assert_called_once_with('session', {'license': 'new_uri'}, None)
            self.assertEqual(res, mock_rights)


    def test_update_rights(self):
        testRights = Rights()
        testRights.source = 'test'
        newRights = {
            'source': 'other',
            'license': 'new_uri'
        }
        testRights.update('session', newRights, [])
        self.assertEqual(testRights.source, 'other')
        self.assertEqual(testRights.license, 'new_uri')

    def test_insert_rights(self):
        newRights = {
            'source': 'other',
            'license': 'new_uri',
            'rights_statement': 'New Rights'
        }
        res = Rights.insert(newRights, [])
        self.assertEqual(res.source, 'other')
        self.assertEqual(res.license, 'new_uri')
        self.assertEqual(res.rights_statement, 'New Rights')
