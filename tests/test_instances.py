import unittest
from unittest.mock import patch, MagicMock
from collections import namedtuple

from model.instance import Instance


class InstanceTest(unittest.TestCase):

    def test_create_instance(self):
        testInst = Instance()
        testInst.title = 'Testing'
        testInst.edition = '1st ed'

        self.assertEqual(str(testInst), '<Instance(title=Testing, edition=1st ed, work=None)>')
    @patch('model.instance.Identifier')
    def test_instance_lookup_new(self, mock_identifier):
        mock_session = MagicMock()
        mock_identifier.getByIdentifier.return_value = None

        res = Instance.lookupInstance(mock_session, ['identifier'], None)
        self.assertEqual(res, None)
    
    @patch('model.instance.Identifier')
    def test_instance_lookup_existing(self, mock_identifier):
        mock_session = MagicMock()
        mock_session.query().filter().one_or_none.return_value = 'vol'
        mock_identifier.getByIdentifier.return_value = 1

        res = Instance.lookupInstance(mock_session, ['identifier'], 'vol')
        self.assertEqual(res, 1)

    @patch('model.instance.Identifier')
    def test_instance_lookup_new_volume(self, mock_identifier):
        mock_session = MagicMock()
        mock_session.query().get.return_value = 'other_vol'
        mock_identifier.getByIdentifier.return_value = 1

        res = Instance.lookupInstance(mock_session, ['identifier'], 'vol')
        self.assertEqual(res, None)
    
    @patch('model.instance.Identifier')
    @patch('model.instance.Instance')
    def test_instance_insert(self, mock_instance, mock_identifier):
        mock_instance.lookupInstance.return_value = None
        mock_instance.insert.return_value = 'new_instance'

        testInst, testOp = Instance.updateOrInsert('session', {})
        self.assertEqual(testInst, 'new_instance')
        self.assertEqual(testOp, 'inserted')
    
    @patch('model.instance.Identifier')
    @patch('model.instance.Instance')
    def test_instance_update(self, mock_instance, mock_identifier):
        mock_instance.lookupInstance.return_value = 1
        mock_session = MagicMock()
        mock_existing = MagicMock()
        mock_session.query().get.return_value = mock_existing

        testInst, testOp = Instance.updateOrInsert(mock_session, {})
        self.assertEqual(testInst, mock_existing)
        self.assertEqual(testOp, 'updated')
    
    @patch('model.instance.Identifier')
    @patch('model.instance.Instance')
    def test_instance_update_work(self, mock_instance, mock_identifier):
        mock_instance.lookupInstance.return_value = 1
        mock_session = MagicMock()
        mock_existing = MagicMock()
        mock_work = MagicMock()
        mock_existing.work = None
        mock_session.query().get.return_value = mock_existing

        testInst, testOp = Instance.updateOrInsert(mock_session, {}, mock_work)
        self.assertEqual(testInst, mock_existing)
        self.assertEqual(mock_existing.work, mock_work)
        self.assertEqual(testOp, 'updated')
