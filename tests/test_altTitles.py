import unittest
from unittest.mock import patch, MagicMock, call

from sfrCore.model import AltTitle
from sqlalchemy.orm.exc import NoResultFound

class AltTitleTest(unittest.TestCase):
    def test_alt_title_repr(self):
        testAlt = AltTitle()
        testAlt.title = 'Testing'
        self.assertEqual(str(testAlt), '<AltTitle(title=Testing, work=[])>')
    
    def test_insertSkip_skip(self):
        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_model.__tablename__ = 'testing'
        res = AltTitle.insertOrSkip(mock_session, 'existing', mock_model, 1)
        self.assertEqual(res, None)

    def test_insertSkip_insert(self):
        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_model.__tablename__ = 'testing'
        mock_session.query().join().filter().filter().one.side_effect = NoResultFound
        newAlt = AltTitle.insertOrSkip(mock_session, 'new', mock_model, 1)
        self.assertIsInstance(newAlt, AltTitle)
        self.assertEqual(newAlt.title, 'new')