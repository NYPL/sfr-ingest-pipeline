import unittest
from unittest.mock import patch, MagicMock, call

from sfrCore.model import Link

class LinkTest(unittest.TestCase):
    def test_link_repr(self):
        testLink = Link()
        testLink.url = 'testURL'
        self.assertEqual(str(testLink), '<Link(url=testURL, media_type=None)>')
    
    @patch.object(Link, 'lookupLink', return_value=None)
    def test_link_updateInsert_insert(self, mock_lookup):
        fakeLink = {'url': 'testing'}
        testLink = Link.updateOrInsert('session', fakeLink, 'testing', 1)
        self.assertIsInstance(testLink, Link)
        self.assertEqual(testLink.url, 'testing')
    
    @patch.object(Link, 'lookupLink')
    def test_link_updateInsert_update(self, mock_lookup):
        fakeLink = {'url': 'testing'}
        mock_existing = MagicMock()
        mock_lookup.return_value = mock_existing
        testLink = Link.updateOrInsert('session', fakeLink, 'testing', 1)
        self.assertEqual(testLink, mock_existing)
    
    def test_link_update(self):
        testLink = Link()
        testLink.url = 'oldURL'

        testLink.update({'url': 'newURL'})
        self.assertEqual(testLink.url, 'newURL')
    
    def test_link_lookup(self):
        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_model.__tablename__ = 'testing'
        mock_session.query().join().filter().filter().one_or_none.return_value = 'testLink'
        testLink = Link.lookupLink(mock_session, {'url': 'test'}, mock_model, 1)
        self.assertEqual(testLink, 'testLink')