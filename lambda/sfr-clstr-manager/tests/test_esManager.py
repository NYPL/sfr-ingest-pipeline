import pytest
from unittest.mock import MagicMock, patch, DEFAULT, call

from helpers.errorHelpers import DataError

from lib.esManager import (
    ElasticManager,
    Work,
    Identifier,
    Language,
    Rights,
    Agent,
    Instance
)


class TestElasticManager(object):
    @pytest.fixture
    def testManager(self):
        mockCreate = patch.object(ElasticManager, 'getCreateWork')
        
        mockCreate.start()
        testElastic = ElasticManager(MagicMock())
        mockCreate.stop()
        
        return testElastic
    
    @pytest.fixture
    def testWorkData(self, testManager):
        testManager.dbWork.alt_titles = ['alt1', 'alt2']
        testManager.dbWork.subjects = [MagicMock(), MagicMock()]
        testManager.dbWork.agent_works = [MagicMock(), MagicMock()]
        testManager.dbWork.identifiers = ['id1', 'id2']
        testManager.dbWork.language = ['lang1', 'lang2']
    
    @pytest.fixture
    def testInstanceData(self):
        testInstance = MagicMock()
        testInstance.title = 'Test Instance'
        testInstance.id = 1
        return testInstance
    
    def test_elasticInit(self, testManager):
        assert isinstance(testManager.dbWork, MagicMock)
        assert isinstance(testManager.work, MagicMock)
    
    def test_createWork_new(self, mocker, testManager):
        testManager.dbWork.title = 'test'
        testManager.dbWork.uuid = 'testUUID'
        mockFields = mocker.patch.object(Work, 'getFields')
        mockFields.return_value = ['title']

        mockGet = mocker.patch.object(Work, 'get')
        mockGet.return_value = None

        newWork = testManager.getCreateWork()

        assert isinstance(newWork, Work)
        assert newWork.title == 'test'

    def test_createWork_existing(self, mocker, testManager):
        testManager.dbWork.title = 'test'
        testManager.dbWork.uuid = 'testUUID'
        mockFields = mocker.patch.object(Work, 'getFields')
        mockFields.return_value = ['title']

        mockGet = mocker.patch.object(Work, 'get')
        mockGet.return_value = 'esWork'

        mockUpdate = mocker.patch.object(ElasticManager, 'updateWork')

        existingWork = testManager.getCreateWork()

        assert existingWork == 'esWork'
        mockUpdate.assert_called_once_with('esWork', {'title': 'test'})
    
    def test_saveWork(self, testManager):
        testManager.saveWork()
        testManager.work.save.assert_called_once()
    
    def test_updateWork(self, testManager):
        mockWork = MagicMock()
        testData = {
            'title': 'testTitle',
            'series': 'testSeries'
        }
        
        testManager.updateWork(mockWork, testData)

        assert mockWork.title == 'testTitle'
        assert mockWork.series == 'testSeries'
    
    def test_enhancedWork(self, mocker, testManager, testWorkData):
        mockDateLoader = MagicMock()
        mockDateLoader.side_effect = [['1999'], ['2000']]
        mockSubject = mocker.patch('lib.esManager.Subject')
        with patch.multiple(ElasticManager,
            addAgent=DEFAULT,
            addIdentifier=DEFAULT,
            addLanguage=DEFAULT,
            addInstances=DEFAULT,
            addGovDocStatus=DEFAULT,
            _loadDates=mockDateLoader
        ) as esMocks:
            testManager.enhanceWork()
            esMocks['addInstances'].assert_called_once()
            esMocks['addGovDocStatus'].assert_called_once()
        
        assert testManager.work.issued_date == '1999'
        assert testManager.work.created_date == '2000'

    def test_addIdentifier_type(self, mocker):
        mockIden = MagicMock()
        mockIden.type = 'test'
        mockTest = MagicMock()
        mockTest.value = 'xxxxxxxxx'

        mockIden.test = [mockTest]

        newIdentifier = ElasticManager.addIdentifier(mockIden)

        assert isinstance(newIdentifier, Identifier)
        assert newIdentifier.id_type == 'test'
        assert newIdentifier.identifier == 'xxxxxxxxx'
    
    def test_addIdentifier_generic(self, mocker):
        mockIden = MagicMock()
        mockIden.type = None
        mockTest = MagicMock()
        mockTest.value = 'xxxxxxxxx'

        mockIden.generic = [mockTest]

        newIdentifier = ElasticManager.addIdentifier(mockIden)

        assert isinstance(newIdentifier, Identifier)
        assert newIdentifier.id_type == 'generic'
        assert newIdentifier.identifier == 'xxxxxxxxx'
    
    def test_addLanguage(self, mocker):
        mockFields = mocker.patch.object(Language, 'getFields')
        mockFields.return_value = ['language', 'iso_2', 'iso_3']
        
        mockLanguage = MagicMock()
        mockLanguage.language = 'testing'
        mockLanguage.iso_2 = 'te'
        mockLanguage.iso_3 = 'tes'

        newLang = ElasticManager.addLanguage(mockLanguage)

        assert isinstance(newLang, Language)
        assert newLang.language == 'testing'
        assert newLang.iso_3 == 'tes'
    
    def test_addRights(self, mocker):
        mockFields = mocker.patch.object(Rights, 'getFields')
        mockFields.return_value = ['license', 'rights_statement']
        
        mockRights = MagicMock()
        mockRights.license = 'CC0'
        mockRights.rights_statement = 'Creative Commons Zero'

        newRights = ElasticManager.addRights(mockRights)

        assert isinstance(newRights, Rights)
        assert newRights.license == 'CC0'
    
    def test_addAgent_new(self, mocker):
        mockRec = MagicMock()
        mockRec.agents = []

        mockRel = MagicMock()
        mockAgent = MagicMock()
        mockRel.agent = mockAgent
        mockRel.role = 'tester'
        mockAgent.name = 'Tester, Test'
        mockAlias = MagicMock()
        mockAlias.alias = 'The Great Testini'
        mockAgent.aliases = [mockAlias]
        mockFields = mocker.patch.object(Agent, 'getFields')
        mockFields.return_value = ['name']

        newAgent = ElasticManager.addAgent(mockRec, mockRel)

        assert isinstance(newAgent, Agent)
        assert newAgent.roles == ['tester']
        assert newAgent.aliases == ['The Great Testini']
        assert newAgent.name == 'Tester, Test'

    def test_addAgent_existing(self):
        mockExisting = MagicMock()
        mockExisting.name = 'Tester'
        mockExisting.roles = ['tester']
    
        mockRec = MagicMock()
        mockRec.agents = [mockExisting]

        mockRel = MagicMock()
        mockAgent = MagicMock()
        mockRel.agent = mockAgent
        mockRel.role = 'approver'
        mockAgent.name = 'Tester'

        ElasticManager.addAgent(mockRec, mockRel)
        assert sorted(mockExisting.roles) == sorted(['tester', 'approver'])
    
    def test_addInstances(self, mocker, testManager):
        mockAdd = mocker.patch.object(ElasticManager, 'addInstance')
        testManager.dbWork.instances = ['inst1', 'inst2', 'inst3']
        
        testManager.addInstances()
        mockAdd.assert_has_calls([call('inst1'), call('inst2'), call('inst3')])
    
    def test_addInstance(self, mocker, testManager, testInstanceData):
        mockDateLoader = MagicMock()
        mockDate = MagicMock()
        mockDate.gte = '2000-01-01'
        mockDate.lte = '2001-01-01'
        mockDateLoader.return_value = [mockDate]

        mockFields = mocker.patch.object(Instance, 'getFields')
        mockFields.return_value = ['title', 'id']

        with patch.multiple(ElasticManager,
            addAgent=DEFAULT,
            addIdentifier=DEFAULT,
            addLanguage=DEFAULT,
            addRights=DEFAULT,
            addItemsData=DEFAULT,
            _loadDates=mockDateLoader
        ) as esMocks:
            newInstance = testManager.addInstance(testInstanceData)
            esMocks['addItemsData'].assert_called_once()

            assert newInstance.title == 'Test Instance'
            assert newInstance.instance_id == 1
            assert newInstance.pub_date_sort == '2000-01-01'
    
    def test_addGovDocStatus_true(self, testManager):
        testManager.dbWork.measurements = [
            MagicMock(quantity='count', value=10),
            MagicMock(quantity='government_document', value=1),
            MagicMock(quantity='holdings', value=0)
        ]
        assert ElasticManager.addGovDocStatus(testManager.dbWork.measurements) == True
    
    def test_addGovDocStatus_false(self, testManager):
        testManager.dbWork.measurements = [
            MagicMock(quantity='count', value=10),
            MagicMock(quantity='government_document', value=0),
            MagicMock(quantity='holdings', value=0)
        ]
        assert ElasticManager.addGovDocStatus(testManager.dbWork.measurements) == False
    
    def test_addGovDocStatus_not_present(self, testManager):
        testManager.dbWork.measurements = [
            MagicMock(quantity='count', value=10),
            MagicMock(quantity='holdings', value=0)
        ]
        assert ElasticManager.addGovDocStatus(testManager.dbWork.measurements) == False
