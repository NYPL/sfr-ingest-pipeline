import unittest
from unittest.mock import patch, MagicMock

from sfrCore.model import Link


class LinkTest(unittest.TestCase):
    def test_link_repr(self):
        testLink = Link()
        testLink.url = 'http://testURL.edu'
        self.assertEqual(
            str(testLink),
            '<Link(url=testurl.edu, media_type=None)>'
        )

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
        self.assertEqual(testLink.url, 'newurl')

    def test_link_lookup(self):
        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_model.__tablename__ = 'testing'
        mock_session.query().join().filter().filter().one_or_none.return_value = 'testLink'
        testLink = Link.lookupLink(mock_session, {'url': 'test'}, mock_model, 1)
        self.assertEqual(testLink, 'testLink')

    def test_url_cleaner(self):
        cleanLink = Link.httpRegexSub('https://www.nypl.org')
        self.assertEqual(cleanLink, 'www.nypl.org')

    def test_url_cleaner_lowercase(self):
        cleanLink = Link.httpRegexSub('http://www.NYPL.org')
        self.assertEqual(cleanLink, 'www.nypl.org')