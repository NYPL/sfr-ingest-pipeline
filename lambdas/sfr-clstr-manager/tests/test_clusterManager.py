import pytest
from unittest.mock import MagicMock, patch, DEFAULT, call

from helpers.errorHelpers import DataError
from lib.clusterManager import ClusterManager, KModel, Edition, Work

class TestClusterManager(object):
    @pytest.fixture
    def testManager(self, mocker):
        mockLogger = mocker.patch('lib.clusterManager.createLog')
        mockLogger.return_value = MagicMock()
        mockParse = patch.object(ClusterManager, 'parseMessage')

        mockManager = MagicMock() # Mock DB Manager object
        
        mockParse.start()
        testCluster = ClusterManager('record', mockManager)
        mockParse.stop()
        return testCluster
    
    @pytest.fixture
    def mockEditions(self):
        return (
            None,
            [
                {
                    'rowID': 1,
                    'pubPlace': 'place1',
                    'pubDate': 'date1',
                    'publisher': 'publisher1',
                    'edition': 'edition1'
                },
                {
                    'rowID': 2,
                    'pubPlace': '',
                    'pubDate': '',
                    'publisher': '',
                    'edition': 'edition2'
                },
                {
                    'rowID': 3,
                    'pubPlace': '',
                    'pubDate': 'date3',
                    'publisher': '',
                    'edition': ''
                }
            ]
        )

    def test_cluster_init(self, testManager):
        assert isinstance(testManager, ClusterManager)
    
    def test_parseMessage_success(self, testManager):
        testManager.parseMessage({'type': 'test', 'identifier': 'xxxxxx'})
        assert testManager.idType == 'test'
        assert testManager.identifier == 'xxxxxx'
    
    def test_parseMessage_success_no_type(self, testManager):
        testManager.parseMessage({'identifier': 'testUUID'})
        assert testManager.idType == 'uuid'
        assert testManager.identifier == 'testUUID'

    def test_parseMessage_error(self, testManager):
        with pytest.raises(DataError):
            testManager.parseMessage({})
    
    def test_clusterInstances(self, mocker, testManager):
        mockFetch = mocker.patch.object(ClusterManager, 'fetchWork')
        mockWork = MagicMock()
        mockFetch.return_value = mockWork
        mockWork.instances = ['inst1', 'inst2']
        mockEditions = MagicMock()
        mocker.patch.multiple(KModel,
            createDF=DEFAULT,
            generateClusters=DEFAULT,
            parseEditions=mockEditions
        )
        mockEditions.return_value = 'editions'
        testManager.clusterInstances()
        assert testManager.work == mockWork
        assert testManager.editions == 'editions'
    
    def test_deleteEditions(self, testManager):
        testManager.work = MagicMock()
        testManager.work.editions = ['ed1', 'ed2']
        mockSession = MagicMock()
        mockDelete = MagicMock()
        testManager.dbManager.createSession.return_value = mockSession
        mockSession.delete = mockDelete
        testManager.deleteExistingEditions()
        mockDelete.assert_has_calls([call('ed1'), call('ed2')])
    
    def test_storeEditions(self, mocker, testManager):
        testManager.editions = ['ed1', 'ed2']
        testManager.work = MagicMock()
        mockCreate = mocker.patch.object(ClusterManager, 'createEdition')
        mockCreate.side_effect = ['ed1', 'ed2']
        mockSession = MagicMock()
        mockAddAll = MagicMock()
        mockSession.add_all = mockAddAll
        testManager.dbManager.createSession.return_value = mockSession
        testManager.storeEditions()
        mockCreate.assert_has_calls([call(mockSession, 'ed1'), call(mockSession, 'ed2')])
        mockAddAll.assert_called_once_with(['ed1', 'ed2'])
    
    def test_createEdition(self, mocker, testManager):
        mockMerge = mocker.patch.object(ClusterManager, 'mergeInstances')
        mergeData = {
            'pubPlace': 'testtown',
            'pubDate': '2019',
            'rowIDs': 0
        }
        mockMerge.return_value = mergeData

        mockCreate = mocker.patch.object(Edition, 'createEdition')
        mockCreate.return_value = True
        
        testManager.work = 'testWork'
        mockFetch = mocker.patch.object(ClusterManager, 'fetchInstances')
        mockFetch.return_value = 0

        newEd = testManager.createEdition('session', 'ed1')
        assert newEd is True
        mockMerge.assert_called_once_with('ed1')
        mockFetch.assert_called_once_with('session', 0)
        mockCreate.assert_called_once_with(mergeData, 'testWork', 0)
    
    def test_mergeInstances_date(self, testManager, mockEditions):
        testEditions = (1900, mockEditions[1])
        out = testManager.mergeInstances(testEditions)
        assert isinstance(out, dict)
        assert out['rowIDs'] == [1, 2, 3]
        assert out['pubPlace'] == 'place1'
        assert out['edition_statement'] == 'edition2'
        assert out['pubDate'] == '[1900-01-01,1900-12-31]'
    
    def test_mergeInstances_no_date(self, testManager, mockEditions):
        testEditions = (0, mockEditions[1])
        out = testManager.mergeInstances(testEditions)
        assert isinstance(out, dict)
        assert out['rowIDs'] == [1, 2, 3]
        assert out['pubPlace'] == 'place1'
        assert out['edition_statement'] == 'edition2'
        assert out['pubDate'] == None

    def test_fetchWork_uuid(self, mocker, testManager):
        testManager.idType = 'uuid'
        testManager.identifier = 'xxxxxxxxx'

        mockGetUUID = mocker.patch.object(Work, 'getByUUID')
        mockGetUUID.return_value = 'testWork'

        outWork = testManager.fetchWork('session')
        assert outWork == 'testWork'
        mockGetUUID.assert_called_once_with('session', 'xxxxxxxxx')
    
    def test_fetchWork_other(self, mocker, testManager):
        testManager.idType = 'test'
        testManager.identifier = 'xxxxxxxxx'

        mockLookup = mocker.patch.object(Work, 'lookupWork')
        mockLookup.return_value = 'testWork'

        outWork = testManager.fetchWork('session')
        assert outWork == 'testWork'
        mockLookup.assert_called_once_with(
            'session',
            [{'type': 'test', 'identifier': 'xxxxxxxxx'}]
        )
    
    def test_fetchInstances(self, testManager):
        mockSession = MagicMock()
        testManager.dbManager.createSession.return_value = mockSession
        mockSession.query().filter().all.return_value = [1, 2, 3]
        testManager.work = 'testWork'
        outInstances = testManager.fetchInstances(mockSession, [1, 2, 3])
        assert outInstances == [1, 2, 3]
