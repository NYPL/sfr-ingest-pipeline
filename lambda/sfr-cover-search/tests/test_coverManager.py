import pytest

from lib.coverManager import CoverManager, SFRCover


class TestCoverManager:
    @pytest.fixture
    def testManager(self, mocker):
        mocker.patch.dict('os.environ', {'UPDATE_PERIOD': '1'})
        mocker.patch('lib.coverManager.OutputManager')
        mocker.patch('lib.coverManager.CCCoverFetcher')
        return CoverManager(mocker.MagicMock(), mocker.MagicMock())

    @pytest.fixture
    def instances(self, mocker):
        return [mocker.MagicMock(), mocker.MagicMock(), mocker.MagicMock()]

    @pytest.fixture
    def identifiers(self, mocker):
        return [
            [
                {'type': 'test', 'value': 1}
            ], [
                {'type': 'test', 'value': 2},
                {'type': 'test', 'value': 3}
            ], [
                {'type': 'test', 'value': 4},
                {'type': 'test', 'value': 5}
            ]
        ]

    @pytest.fixture
    def idValidators(self, mocker):
        testId1 = mocker.MagicMock()
        testId1.type = 'tester'
        id1Value = mocker.MagicMock()
        id1Value.value = 1
        testId1.tester = [id1Value]

        testId2 = mocker.MagicMock()
        testId2.type = 'isbn'
        id2Value = mocker.MagicMock()
        id2Value.value = 9781234567890
        testId2.isbn = [id2Value]

        return [testId1, testId2]

    @pytest.fixture
    def covers(self):
        class TestCover(SFRCover):
            def __init__(self, uri, source, mediaType, instanceID):
                super().__init__(uri, source, mediaType, instanceID)
        return [
            TestCover(test[0], test[1], test[2], test[3])
            for test in [
                ('uri1', 'testing', 'testType', 1),
                ('uri2', 'testing', 'testType', 2)
            ]
        ]

    def test_manager_init(self, testManager):
        assert testManager.updatePeriod == '1'
        assert len(testManager.fetchers) == 3
        assert testManager.covers == []

    def test_getInstancesForSearch(self, testManager, mocker):
        mockSession = mocker.MagicMock()
        testManager.manager.createSession.return_value = mockSession
        mockSession.query()\
            .outerjoin().filter().group_by().having()\
            .all.return_value = [1, 2, 3]
        testManager.getInstancesForSearch()
        assert testManager.instances == [1, 2, 3]

    def test_getCoversForInstances(self,
                                   testManager, instances,
                                   identifiers, mocker):
        testManager.instances = instances
        mocker.patch.object(
            CoverManager,
            'getValidIDs',
            side_effect=identifiers
        )
        mockSearchIdentifiers = mocker.patch.object(
            CoverManager, 'searchInstanceIdentifiers'
        )
        testManager.getCoversForInstances()
        mockSearchIdentifiers.assert_has_calls([
            mocker.call(instances[0], [{'type': 'test', 'value': 1}]),
            mocker.call(
                instances[1],
                [{'type': 'test', 'value': 2}, {'type': 'test', 'value': 3}]
            ),
            mocker.call(
                instances[2],
                [{'type': 'test', 'value': 4}, {'type': 'test', 'value': 5}]
            )
        ])

    def test_searchInstanceIdentifiers(self, testManager, identifiers, mocker):
        mockQuery = mocker.patch.object(CoverManager, 'queryFetchers')
        mockFetcher = mocker.MagicMock()
        mockQuery.side_effect = [(None, None), (mockFetcher, 1)]

        mockInstance = mocker.MagicMock()
        mockInstance.id = 1
        identifiers = identifiers[1]
        mocker.patch('lib.coverManager.SFRCover', return_value=True)

        testManager.searchInstanceIdentifiers(mockInstance, identifiers)
        assert testManager.covers[0] is True
        mockQuery.assert_has_calls([
            mocker.call('test', 2), mocker.call('test', 3)
        ])

    def test_queryFetchers(self, testManager, mocker):
        testManager.fetchers = (mocker.MagicMock(), mocker.MagicMock())
        testManager.fetchers[0].queryIdentifier.return_value = None
        testManager.fetchers[1].queryIdentifier.return_value = 'testID'

        outFetcher = testManager.queryFetchers('test', 1)

        assert outFetcher[0] == testManager.fetchers[1]
        assert outFetcher[1] == 'testID'

    def test_queryFetchers_notFound(self, testManager, mocker):
        testManager.fetchers = (mocker.MagicMock(), mocker.MagicMock())
        testManager.fetchers[0].queryIdentifier.return_value = None
        testManager.fetchers[1].queryIdentifier.return_value = None

        outFetcher = testManager.queryFetchers('test', 1)

        assert outFetcher == (None, None)

    def test_getValidIDs(self, idValidators):
        validatedIDs = CoverManager.getValidIDs(idValidators)
        assert len(validatedIDs) == 1
        assert validatedIDs[0]['type'] == 'isbn'
        assert validatedIDs[0]['value'] == 9781234567890

    def test_sendCoversToKinesis(self, testManager, covers, mocker):
        mocker.patch.dict('os.environ', {'KINESIS_INGEST_STREAM': 'test'})
        testManager.covers = covers
        testManager.output = mocker.MagicMock()

        testManager.sendCoversToKinesis()
        testManager.output.putKinesis.assert_has_calls([
            mocker.call(
                {
                    'uri': 'uri1',
                    'source': 'testing',
                    'mediaType': 'testType',
                    'instanceID': 1
                },
                'test',
                recType='cover'
            ),
            mocker.call(
                {
                    'uri': 'uri2',
                    'source': 'testing',
                    'mediaType': 'testType',
                    'instanceID': 2
                },
                'test',
                recType='cover'
            )
        ])
