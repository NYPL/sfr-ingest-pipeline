import pytest
from unittest.mock import patch, DEFAULT, call, MagicMock

from lib.models.metRecord import MetItem
from lib.dataModel import WorkRecord, InstanceRecord, Format


class TestMETItem:
    @pytest.fixture
    def testItem(self):
        return MetItem(1, {})

    @pytest.fixture
    def parentData(self):
        return {
            'parent': {
                'fields': [
                    {'key': 1, 'value': 'test1'},
                    {'key': 2, 'value': 'test2'},
                    {'key': 3, 'value': 'test3'}
                ]
            },
            'downloadUri': '/download/1',
            'imageUri': '/cover/1'
        }

    @pytest.fixture
    def standardData(self):
        return {
            'fields': [
                {'key': 1, 'value': 'test1'},
                {'key': 2, 'value': 'test2'},
                {'key': 3, 'value': 'test3'}
            ],
            'downloadUri': '/download/1',
            'imageUri': '/cover/1',
            'parent': None
        }

    def test_init(self, testItem):
        assert testItem.itemID == 1
        assert testItem.data == {}
        assert isinstance(testItem.work, WorkRecord)
        assert isinstance(testItem.instance, InstanceRecord)
        assert isinstance(testItem.item, Format)
        assert testItem.item.source == 'met'

    def test_extractRelevantData_parent(self, testItem, parentData):
        with patch.object(MetItem, 'transformFields') as mockTransform:
            mockTransform.return_value = 'dataDict'
            testItem.data = parentData
            testItem.extractRelevantData()
            mockTransform.assert_called_once_with(parentData['parent']['fields'])
            assert testItem.fields == 'dataDict'
            assert testItem.coverURI == '/cover/1'
            assert testItem.viewURI == MetItem.ITEM_UI.format(1)

    def test_extractRelevantData_standard(self, testItem, standardData):
        with patch.object(MetItem, 'transformFields') as mockTransform:
            mockTransform.return_value = 'dataDict'
            testItem.data = standardData
            testItem.extractRelevantData()
            mockTransform.assert_called_once_with(standardData['fields'])
            assert testItem.fields == 'dataDict'
            assert testItem.coverURI == '/cover/1'
            assert testItem.viewURI == MetItem.ITEM_UI.format(1)

    def test_transformFields(self, testItem, standardData):
        outDict = testItem.transformFields(standardData['fields'])
        assert outDict[2]['value'] == 'test2'

    def test_createStructure(self, testItem):
        testItem.fields = testItem.transformFields([
            {'key': 'title', 'value': 'testTitle'},
            {'key': 'publis', 'value': 'testPublisher'},
            {'key': 'source', 'value': 'testSource'}
        ])
        testItem.createStructure()
        assert testItem.work.title == 'testTitle'
        assert testItem.instance.publisher == 'testPublisher'
        assert testItem.item.provider == 'testSource'

    def test_parseIdentifiers(self, testItem):
        testItem.work['identifier.test'] = 1
        testItem.instance['identifier.test'] = 2
        testItem.item['identifier.test'] = 3

        testItem.parseIdentifiers()
        assert len(testItem.work.identifiers) == 1
        assert len(testItem.instance.identifiers) == 1
        assert len(testItem.item.identifiers) == 1
        assert testItem.work.primary_identifier.identifier == 1
        assert testItem.work.primary_identifier.type == 'test' 
    
    def test_parseSubjects(self, testItem):
        testItem.work.subjects = 'testSubj1 ; testSubj2 ; testSubj3'
        testItem.parseSubjects()
        assert len(testItem.work.subjects) == 3
        assert testItem.work.subjects[2].subject == 'testSubj3'

    def test_parseAgents(self, testItem):
        with patch.object(MetItem, 'parseAgent') as mockParse:
            testItem.parseAgents()
            mockParse.assert_has_calls([
                call('work', 'author'),
                call('instance', 'publisher'),
                call('item', 'repository'),
                call('item', 'provider')
            ])
        
    def test_parseAgent_success(self, testItem):
        testItem.work.author = 'Tester, Test'
        testItem.parseAgent('work', 'author')
        assert testItem.work.agents[0].name == 'Tester, Test'

    def test_parseAgent_missing(self, testItem):
        testItem.parseAgent('work', 'author')
        assert len(testItem.work.agents) == 0

    def test_parseRights_publicdomain(self, testItem):
        for rec in [testItem.instance, testItem.item]:
            rec.license = 'Public Domain'
            rec.rights_statement = 'Released into the Public Domain'
            rec.rights_reason = 'A reason for this determination'
        testItem.parseRights()
        assert len(testItem.instance.rights) == 1
        assert testItem.item.rights[0].license == 'public_domain'
        assert testItem.item.rights[0].source == 'met'

    def test_parseRights_copyrighted(self, testItem):
        for rec in [testItem.instance, testItem.item]:
            rec.license = 'copyrighted'
            rec.rights_statement = 'Test Copyright statement'
            rec.rights_reason = 'A reason for this determination'
        testItem.parseRights()
        assert len(testItem.instance.rights) == 1
        assert testItem.item.rights[0].license == 'uncertain'
        assert testItem.item.rights[0].rights_statement == 'Refer to Material for Copyright'

    def test_parseLanguages_success(self, testItem):
        for rec in [testItem.work, testItem.instance]:
            rec.language = 'german'
        
        testItem.parseLanguages()
        print(testItem.work.language)
        assert testItem.work.language[0].iso_2 == 'de'
        assert testItem.instance.language[0].iso_3 == 'deu'

    def test_parseLanguages_failure(self, testItem):
        for rec in [testItem.work, testItem.instance]:
            rec.language = 'testing'
        
        testItem.parseLanguages()
        print(testItem.work.language)
        assert testItem.work.language == []
        assert testItem.instance.language == []

    def test_parseDates(self, testItem):
        testItem.instance.publication_date = '2020'
        testItem.parseDates()
        assert testItem.instance.dates[0].date_range == '2020'
        assert testItem.instance.dates[0].date_type == 'publication_date'
        assert getattr(testItem.instance, 'publication_date', None) == None

    def test_parseLinks(self, testItem):
        testItem.viewURI = 'testView'
        testItem.downloadURI = '/testDownload'
        testItem.parseLinks()

        assert testItem.item.links[0].media_type == 'text/html'
        assert testItem.item.links[0].url == 'testView'
        assert testItem.item.links[1].media_type == 'application/pdf'
        assert testItem.item.links[1].flags['download'] == True

    def test_addCover(self, testItem):
        testItem.coverURI = '/cover/1'
        testItem.addCover()
        assert testItem.instance.links[0].media_type == 'image/jpeg'
        assert testItem.instance.links[0].url == '{}/cover/1'.format(testItem.ROOT_URL)
        assert testItem.instance.links[0].flags['cover'] == True
