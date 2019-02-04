import unittest
from unittest.mock import patch
from collections import namedtuple

from model.rights import Rights

RightsTup = namedtuple('TestRights',
    ['id', 'source', 'license', 'rights_statement', 'rights_reason', 'dates']
)


class TestRights(unittest.TestCase):

    @patch('model.rights.Rights.lookupRights', return_value=None)
    @patch('model.rights.Rights.insert', return_value=True)
    def test_check_new(self, mock_insert, mock_lookup):
        res = Rights.updateOrInsert(
            'session',
            {'license': 'rghts'},
            'Rights',
            1
        )
        mock_lookup.expect_to_be_called()
        self.assertTrue(res)

    tr = RightsTup(
        id=1,
        source='test',
        license='rights_uri',
        rights_statement='Sample Statement',
        rights_reason='Sample Reason',
        dates=[]
    )
    @patch('model.rights.Rights.lookupRights', return_value=tr)
    @patch('model.rights.Rights.update')
    def test_check_existing(self, mock_update, mock_lookup):
        res = Rights.updateOrInsert(
            'session',
            {'license': 'new_uri'},
            'Date',
            1
        )
        mock_lookup.expect_to_be_called()
        mock_update.expect_to_be_called()
        self.assertEqual(res, None)


    def test_update_rights(self):
        newTest = Rights.insert({
            'id': 1,
            'source': 'test',
            'license': 'rights_uri',
            'rights_statement': 'Sample Statement',
            'rights_reason': 'Sample Reason',
        }, dates=[])
        newRights = {
            'source': 'other',
            'license': 'new_uri'
        }
        Rights.update('session', newTest, newRights)
        self.assertEqual(newTest.source, 'other')
        self.assertEqual(newTest.license, 'new_uri')

    def test_insert_rights(self):
        newRights = {
            'source': 'other',
            'license': 'new_uri',
            'rights_statement': 'New Rights'
        }
        res = Rights.insert(newRights)
        self.assertEqual(res.source, 'other')
        self.assertEqual(res.license, 'new_uri')
        self.assertEqual(res.rights_statement, 'New Rights')
