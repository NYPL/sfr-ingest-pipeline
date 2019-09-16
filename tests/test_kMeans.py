from collections import defaultdict
from pandas import DataFrame
import pytest
from unittest.mock import MagicMock, patch, DEFAULT, call

from helpers.errorHelpers import DataError

from lib.kMeansModel import KModel, TextSelector, NumberSelector


class TestKMeansModel(object):
    @pytest.fixture
    def testModel(self):
        return KModel([])
    
    @pytest.fixture
    def testInstances(self, testModel):
        testModel.instances = [
            TestKMeansModel.createInstance(
                pub_place='test',
                dates=['date1', 'date2'],
                agent_instances=['agent1', 'agent2'],
                edition_statement=['edition1'],
                id=1
            ),
            TestKMeansModel.createInstance(
                pub_place=False,
                dates=None,
                agent_instances=None,
                edition_statement=['edition1'],
                id=2
            ),
            TestKMeansModel.createInstance(
                pub_place='test',
                dates=['date1'],
                agent_instances=['agent2', 'agent3'],
                edition_statement=['edition1'],
                id=3
            )
        ]
    
    @pytest.fixture
    def testClusters(self, testModel):
        testModel.clusters = {
            0: [
                DataFrame({
                    'pubDate': 1900,
                    'publisher': 'test',
                    'place': 'testtown',
                    'rowID': 1,
                    'edition': ''
                }, index=[0]),
                DataFrame({
                    'pubDate': 1900,
                    'publisher': 'test',
                    'place': 'testtown',
                    'rowID': 2,
                    'edition': ''
                }, index=[0])
            ],
            1: [
                DataFrame({
                    'pubDate': 2000,
                    'publisher': 'test',
                    'place': 'testtown',
                    'rowID': 3,
                    'edition': ''
                }, index=[0]),
                DataFrame({
                    'pubDate': 1950,
                    'publisher': 'test',
                    'place': 'testtown',
                    'rowID': 4,
                    'edition': ''
                }, index=[0])
            ]
        }

    @staticmethod
    def createInstance(**kwargs):
        mockInst = MagicMock()
        for key, value in kwargs.items():
            setattr(mockInst, key, value)
        return mockInst
    
    @staticmethod
    def createDate(**kwargs):
        mockDate = MagicMock()
        mockDate.display_date = kwargs.get('display_date', None)
        mockDate.date_type = kwargs.get('date_type', None)
        mockRange = MagicMock()
        mockLower = MagicMock()
        mockUpper = MagicMock()
        mockLower.year, mockUpper.year = kwargs.get('date_range', (None, None))
        mockRange.lower = mockLower
        mockRange.upper = mockUpper
        mockDate.date_range = mockRange

        return mockDate
    
    @staticmethod
    def createAgent(role=None, name=None):
        mockRel = MagicMock()
        mockRel.role = role
        mockAgent = MagicMock()
        mockAgent.name = name
        mockRel.agent = mockAgent
        return mockRel

    def test_kModel_init(self, testModel):
        assert testModel.instances == []
        assert testModel.df == None
        assert isinstance(testModel.clusters, defaultdict)
    
    def test_pubProcessor_str(self):
        cleanStr = KModel.pubProcessor('Testing & Testing,')
        assert cleanStr == 'testing and testing'

        cleanStr2 = KModel.pubProcessor('[publisher not identified]')
        assert cleanStr2 == ''
    
    def test_pubProcessor_list(self):
        cleanStr = KModel.pubProcessor(['hello', 'sn', 'goodbye'])
        assert cleanStr == 'hello goodbye'
    
    def test_pubProcessor_none(self):
        cleanStr = KModel.pubProcessor(None)
        assert cleanStr == ''
    
    def test_createDF(self, mocker, testModel, testInstances):
        mockGetPub = mocker.patch.object(KModel, 'getPublisher')
        mockGetPub.side_effect = [
            'agent1; agent2',
            False,
            False
        ]
        mockGetDate = mocker.patch.object(KModel, 'getPubDateFloat')
        mockGetDate.side_effect = [
            1900,
            False,
            1901
        ]

        testModel.createDF()
        assert isinstance(testModel.df, DataFrame)
        assert testModel.df.iloc[0]['rowID'] == 1
        assert testModel.df.iloc[1]['rowID'] == 3
        assert testModel.maxK == 2

    def test_getPubDateFloat_both(self):
        mockDates = [
            TestKMeansModel.createDate(date_type='other_date'),
            TestKMeansModel.createDate(
                date_type='pub_date',
                date_range=(1900, 1901),
                date_display='1900-1901'
            )
        ]
        outYear = KModel.getPubDateFloat(mockDates)
        assert outYear == 1900.5
    
    def test_getPubDateFloat_upper(self):
        mockDates = [
            TestKMeansModel.createDate(date_type='other_date'),
            TestKMeansModel.createDate(
                date_type='pub_date',
                date_range=(None, 1901),
                date_display='1900-1901'
            )
        ]
        outYear = KModel.getPubDateFloat(mockDates)
        assert outYear == 1901
    
    def test_getPubDateFloat_lower(self):
        mockDates = [
            TestKMeansModel.createDate(date_type='other_date'),
            TestKMeansModel.createDate(
                date_type='pub_date',
                date_range=(1900, None),
                date_display='1900-1901'
            )
        ]
        outYear = KModel.getPubDateFloat(mockDates)
        assert outYear == 1900
    
    def test_getPubDateFloat_neither(self):
        mockDates = [
            TestKMeansModel.createDate(date_type='other_date'),
            TestKMeansModel.createDate(
                date_type='pub_date',
                date_display='1900-1901'
            )
        ]
        outYear = KModel.getPubDateFloat(mockDates)
        assert outYear == 0
    
    def test_getPublisher(self):
        mockAgents = [
            TestKMeansModel.createAgent(role='other', name='other'),
            TestKMeansModel.createAgent(role='publisher', name='Test'),
            TestKMeansModel.createAgent(role='publisher', name='Test2'),
            TestKMeansModel.createAgent(role='publisher', name='Test')
        ]
        outPublisher = KModel.getPublisher(mockAgents)

        assert outPublisher == 'Test; Test2'
    
    def test_generateClusters_multiple(self, mocker, testModel):
        mockGetK = mocker.patch.object(KModel, 'getK')
        testModel.k = 2

        mockCluster = mocker.patch.object(KModel, 'cluster')
        mockCluster.return_value = [
            0, 1, 0
        ]

        testModel.df = DataFrame(['row1', 'row2', 'row3'])

        testModel.generateClusters()
        assert testModel.clusters[0][0].iloc[0][0] == 'row1'
        assert testModel.clusters[0][1].iloc[0][0] == 'row3'
        assert testModel.clusters[1][0].iloc[0][0] == 'row2'
    
    def test_generateClusters_single(self, mocker, testModel):
        mockGetK = mocker.patch.object(KModel, 'getK')
        mockGetK.side_effect = ZeroDivisionError

        mockCluster = mocker.patch.object(KModel, 'cluster')
        mockCluster.side_effect = ValueError
        testModel.instances = ['row1']
        testModel.df = DataFrame(['row1'])

        testModel.generateClusters()
        assert testModel.clusters[0][0].iloc[0][0] == 'row1'        

    def test_cluster_score(self, mocker, testModel):
        mockPipeline = MagicMock()
        
        def fakeGet(self, key):
            mockGet = MagicMock()
            mockGet.inertia_ = 1
            if key == 'kmeans':
                return mockGet   
            return MagicMock()

        mockCreate = mocker.patch.object(KModel, 'createPipeline')
        mockCreate.return_value = mockPipeline
        mockPipeline.__getitem__ = fakeGet

        out = testModel.cluster(1, score=True)
        assert out == 1
        mockPipeline.fit.assert_called_once()
    
    def test_cluster_predict(self, mocker, testModel):
        mockPipeline = MagicMock()
        mockCreate = mocker.patch.object(KModel, 'createPipeline')
        mockCreate.return_value = mockPipeline

        testModel.cluster(1)
        mockCreate.assert_called_once()
        mockPipeline.fit_predict.assert_called_once()

    def test_parseEditions(self, mocker, testModel, testClusters):
        outEditions = testModel.parseEditions()
        assert len(outEditions) == 3
        assert outEditions[1][0] == 1950