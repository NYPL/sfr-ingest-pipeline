import unittest
from unittest.mock import patch, MagicMock, call

from sfrCore.model import Equivalent


class TestEquivalent(unittest.TestCase):
    
    def test_create_equivalency(self):
        equiv = Equivalent(
            source_id=1,
            target_id=2,
            type='test',
            match_data={'test': 'test'}
        )
        self.assertEqual(
            str(equiv),
            '<Equivalency(source=1, target=2, type=test)>'
        )

    def test_create_function(self):
        equiv = Equivalent.createEquivalency(
            1,
            2,
            'test',
            {'test': 'test'}
        )
        self.assertEqual(
            str(equiv),
            '<Equivalency(source=1, target=2, type=test)>'
        )
    
    @patch('sfrCore.model.Equivalent.createEquivalency', side_effect=[1,2])
    def test_add_equivalencies(self, mock_add):
        mock_session = MagicMock()
        Equivalent.addEquivalencies(
            mock_session,
            1, 
            ['test1', 'test2'],
            'test',
            {'test': 'test'}
        )
        mock_session.add.assert_has_calls([call(1), call(2)])
