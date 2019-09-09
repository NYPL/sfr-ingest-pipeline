import unittest
from unittest.mock import patch, MagicMock, call, DEFAULT

from sfrCore.model import Work, Edition


class EditionTest(unittest.TestCase):
    def test_new_edition(self):
        testWork = Work()
        testEdition = Edition(
            pubDate='2019-01-01',
            pubPlace='testing',
            work=testWork
        )
        self.assertEqual(str(testEdition), '<Edition(place=testing, date=2019-01-01, publisher=)>')

    @patch('sfrCore.model.edition.Edition.addMetadata')
    @patch('sfrCore.model.edition.Edition.addInstances')
    def test_create_edition(self, mock_inst, mock_meta):
        testMeta = {
            'pubPlace': 'testing',
            'pubDate': '2019-01-01',
            'edition': '1st test'
        }
        testEdition = Edition.createEdition(testMeta, MagicMock(), [1, 2, 3])

        self.assertEqual(testEdition.publication_place, 'testing')
        mock_meta.assert_called_once_with({'edition': '1st test'})
        mock_inst.assert_called_once_with([1, 2, 3])

    def test_addMetadata(self):
        testMetadata = {
            'edition': 'testing',
            'volume': 'test vol',
            'summary': 'testing summary'
        }
        testEdition = Edition()
        testEdition.addMetadata(testMetadata)
        self.assertEqual(testEdition.summary, 'testing summary')

    def test_addInstances(self):
        testInst1 = MagicMock()
        testInst2 = MagicMock()
        testEdition = Edition()
        testEdition.addInstances([testInst1, testInst2])
        self.assertEqual(len(list(testEdition.instances)), 2)

    def test_getExistingEdition(self):
        mock_session = MagicMock()
        mock_work = MagicMock()
        mock_session\
            .query.join.filter.filter.group_by.having\
            .one_or_none.return_value = True
        self.assertTrue(Edition.getExistingEdition(
            mock_session,
            mock_work,
            [MagicMock(), MagicMock()]
        ))

    def test_loadPublishers(self):
        mockInst1 = MagicMock()
        mockAgent1 = MagicMock()
        mockAgent1.role = 'publisher'
        mockAgent1.agent.name = 'Test, Tester'
        mockAgent2 = MagicMock()
        mockAgent2.role = 'other'
        mockInst1.agent_instances = [mockAgent1, mockAgent2]

        mockInst2 = MagicMock()
        mockInst2.agent_instances = [mockAgent1]

        testEdition = Edition()
        testEdition.instances = {mockInst1, mockInst2}
        publishers = testEdition.loadPublishers()

        self.assertEqual(publishers, 'Test, Tester')
