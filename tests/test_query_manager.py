import unittest
from unittest.mock import patch, MagicMock, call, DEFAULT

from lib.outputManager import OutputManager
from lib.queryManager import (
    queryWork, getIdentifiers, getAuthors, createClassifyQuery
)


class TestQueryManager(unittest.TestCase):
    @patch('lib.queryManager.getIdentifiers', return_value=[])
    @patch('lib.queryManager.getAuthors', return_value='auth1, auth2')
    @patch('lib.queryManager.createClassifyQuery')
    def test_queryWork_noIdentifiers(self, mockQuery, mockAuth, mockGet):
        mockWork = MagicMock()
        mockWork.title = 'testTitle'
        mockWork.agent_works = ['auth1', 'auth2']
        queryWork('session', mockWork, 'testUUID')
        mockGet.assert_called_once_with('session', mockWork)
        mockAuth.assert_called_once_with(['auth1', 'auth2'])
        mockQuery.assert_called_once_with(
            {'title': 'testTitle', 'authors': 'auth1, auth2'},
            'authorTitle',
            'testUUID'
        )

    @patch('lib.queryManager.getIdentifiers')
    @patch('lib.queryManager.createClassifyQuery')
    def test_queryWork_identifiers(self, mockQuery, mockGet):
        mockGet.return_value = {
            'testing': [1, 2, 3]
        }
        mockWork = MagicMock()
        queryWork('session', mockWork, 'test')
        mockGet.assert_called_once_with('session', mockWork)
        mockQuery.assert_has_calls([
            call({'idType': 'testing', 'identifier': 1}, 'identifier', 'test'),
            call({'idType': 'testing', 'identifier': 2}, 'identifier', 'test'),
            call({'idType': 'testing', 'identifier': 3}, 'identifier', 'test')
        ])

    def test_getIdentifiers(self):
        mockSession = MagicMock()
        mockSession.query().join().filter().all.side_effect = [
            [],
            [],
            [],
            [(1,), (2,), (3,)],
            []
        ]
        testIdentifiers = getIdentifiers(mockSession, MagicMock())
        self.assertEqual(testIdentifiers, {'lccn': [1, 2, 3]})

    def test_getAuthors(self):
        mockRel1 = MagicMock()
        mockRel1.role = 'author'
        mockAgent1 = MagicMock()
        mockAgent1.name = 'agent1'
        mockRel1.agent = mockAgent1

        mockRel2 = MagicMock()
        mockRel2.role = 'other'
        mockAgent2 = MagicMock()
        mockAgent2.name = 'agent2'
        mockRel2.agent = mockAgent2

        testAgents = getAuthors([mockRel1, mockRel2])
        self.assertEqual(testAgents, 'agent1')

    @patch.dict('os.environ', {'CLASSIFY_QUEUE': 'testQueue'})
    @patch.multiple(OutputManager, checkRecentQueries=DEFAULT)
    def test_createClassifyQuery_noCache(self, checkRecentQueries):
        testQuery = {
            'idType': 'testing',
            'identifier': '1'
        }
        checkRecentQueries.return_value = False
        outMsg = createClassifyQuery(testQuery, 'test', 'uuid')
        checkRecentQueries.assert_called_once_with('testing/1')
        self.assertEqual(outMsg['fields']['identifier'], '1')
        self.assertEqual(outMsg['type'], 'test')

    @patch.dict('os.environ', {'CLASSIFY_QUEUE': 'testQueue'})
    @patch.multiple(OutputManager,
                    checkRecentQueries=DEFAULT, putQueue=DEFAULT)
    def test_createClassifyQuery_cached(self, checkRecentQueries, putQueue):
        testQuery = {
            'idType': 'testing',
            'identifier': '1'
        }
        createClassifyQuery(testQuery, 'test', 'uuid')
        checkRecentQueries.assert_called_once_with('testing/1')
        putQueue.assert_not_called()
