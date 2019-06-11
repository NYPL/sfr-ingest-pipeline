import unittest
from unittest.mock import patch, MagicMock, call

from sfrCore.model import Subject

class SubjectTest(unittest.TestCase):
    def test_subject_repr(self):
        testSubject = Subject()
        testSubject.authority = 'test'
        testSubject.subject = 'subject'
        self.assertEqual(str(testSubject), '<Subject(subject=subject, uri=None, authority=test)>')
    
    @patch.object(Subject, 'lookupSubject', return_value=None)
    @patch.object(Subject, 'insert', return_value='newSubject')
    def test_subject_updateInsert_insert(self, mock_insert, mock_lookup):
        fakeSubject = {'authority': 'test'}
        testSubject = Subject.updateOrInsert('session', fakeSubject)
        self.assertEqual(testSubject, 'newSubject')
    
    @patch.object(Subject, 'lookupSubject')
    def test_measure_updateInsert_update(self, mock_lookup):
        fakeSubject = {'authority': 'test'}
        mock_existing = MagicMock()
        mock_lookup.return_value = mock_existing
        testSubject = Subject.updateOrInsert('session', fakeSubject)
        self.assertEqual(testSubject, mock_existing)
    
    @patch.object(Subject, 'addMeasurements')
    def test_subject_insert(self, mock_measure):
        testSubject = Subject.insert({'authority': 'test'}, [])
        self.assertIsInstance(testSubject, Subject)
        self.assertEqual(testSubject.authority, 'test')
        mock_measure.assert_called_once()

    @patch.object(Subject, 'updateMeasurements')
    def test_subject_update(self, mock_measure):
        testSubject = Subject()
        testSubject.authority = 'test'

        testSubject.update('session', {'authority': 'newTest'}, [])
        self.assertEqual(testSubject.authority, 'newTest')
        mock_measure.assert_called_once()
    
    def test_subject_lookup_success(self):
        mock_session = MagicMock()
        mock_session.query()\
            .filter().filter()\
            .one_or_none.return_value = 'testSubject'
        testSubject = Subject.lookupSubject(mock_session, {'authority': 'test', 'subject': 'subj'})
        self.assertEqual(testSubject, 'testSubject')