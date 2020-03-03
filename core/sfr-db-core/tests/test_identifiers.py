import unittest
from unittest.mock import MagicMock

from sfrCore.helpers import DataError
from sfrCore.model import Identifier


class TestIdentifiers(unittest.TestCase):
    def test_found_single_identifier(self):
        mock_session = MagicMock()
        mock_session.execute.return_value = [(1,)]
        mock_instance = MagicMock()
        mock_instance.__tablename__ = 'testing'
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
        mock_session.execute.return_value = []
        mock_instance = MagicMock()
        mock_instance.__tablename__ = 'testing'
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
        mock_session.execute.return_value = [(1,)]
        mock_instance = MagicMock()
        mock_instance.__tablename__ = 'testing'
        ids = [
            {
                'identifier': '123456789',
                'type': None
            }
        ]

        result = Identifier.getByIdentifier(mock_instance, mock_session, ids)
        self.assertEqual(result, 1)

    def test_skip_identifier(self):
        mock_session = MagicMock()
        mock_session.execute.return_value = [(1,)]
        mock_instance = MagicMock()
        mock_instance.__tablename__ = 'testing'
        ids = [
            {
                'identifier': '1234567890',
                'type': 'isbn'
            }, {
                'identifier': '999.99',
                'type': 'ddc'
            }
        ]

        result = Identifier.getByIdentifier(mock_instance, mock_session, ids)
        self.assertEqual(result, 1)

    def test_multi_identifier(self):
        mock_session = MagicMock()
        mock_session.execute.side_effect = [
            [(1,), (2,)],
            [(1,)]
        ]
        mock_instance = MagicMock()
        mock_instance.__tablename__ = 'test_table'
        ids = [
            {
                'identifier': '1234567890',
                'type': 'isbn'
            }, {
                'identifier': '0987654321',
                'type': 'oclc'
            }
        ]

        result = Identifier.getByIdentifier(mock_instance, mock_session, ids)
        self.assertEqual(result, 1)

    def test_clean_id(self):
        testIden = {'identifier': 'id (test)', 'type': 'testing'}
        clean = Identifier._cleanIdentifier(testIden)
        assert clean['type'] == 'testing'
        assert clean['identifier'] == 'id'

    def test_clean_error(self):
        with self.assertRaises(DataError):
            testIden = {'identifier': 'NAN'}
            Identifier._cleanIdentifier(testIden)
