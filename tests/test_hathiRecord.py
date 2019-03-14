import unittest
from unittest.mock import MagicMock
from datetime import datetime

from lib.hathiRecord import HathiRecord
from lib.dataModel import (
    WorkRecord,
    InstanceRecord,
    Format,
    Identifier,
    Agent,
    Rights
)


class TestHathi(unittest.TestCase):
    def test_hathi_create(self):
        testRec = {
            'htid': 1,
            'title': 'Test Record'
        }
        hathiRec = HathiRecord(testRec)
        self.assertIsInstance(hathiRec, HathiRecord)
        self.assertEqual(hathiRec.ingest['htid'], 1)

    def test_hathi_create_date(self):
        testRec = {
            'htid': 1,
            'title': 'Test Record'
        }
        testDate = datetime.strptime('2019-01-01', '%Y-%m-%d')
        hathiRec = HathiRecord(testRec, ingestDateTime=testDate)
        self.assertEqual(
            hathiRec.modified,
            testDate.strftime('%Y-%m-%d %H:%M:%S')
        )

    def test_hathi_create_date_string(self):
        testRec = {
            'htid': 1,
            'title': 'Test Record'
        }
        hathiRec = HathiRecord(testRec, ingestDateTime='2019-01-01')
        self.assertEqual(hathiRec.modified, '2019-01-01')

    def test_hathi_repr(self):
        testRec = {
            'htid': 1,
            'title': 'Test Record'
        }
        hathiRec = HathiRecord(testRec)
        hathiRec.work.title = hathiRec.ingest['title']
        self.assertEqual(str(hathiRec), '<Hathi(title=Test Record)>')

    def test_build_data_model(self):
        testRow = {
            'title': 'Work Test',
            'description': '1st of 4',
            'bib_key': '0000000',
            'htid': 'test.000000000',
            'gov_doc': 'f',
            'author': 'Author, Test',
            'copyright_date': '2019',
            'rights': 'test_rights'
        }
        workTest = HathiRecord(testRow)

        workTest.buildWork = MagicMock()
        workTest.buildInstance = MagicMock()
        workTest.buildItem = MagicMock()
        workTest.createRights = MagicMock()

        workTest.buildDataModel('countryCodes')
        self.assertIsInstance(workTest, HathiRecord)

    def test_build_work(self):
        testRow = {
            'title': 'Work Test',
            'description': '1st of 4',
            'bib_key': '0000000',
            'htid': 'test.000000000',
            'gov_doc': 'f',
            'author': 'Author, Test',
            'copyright_date': '2019'
        }
        workTest = HathiRecord(testRow)
        workTest.parseIdentifiers = MagicMock()
        workTest.parseAuthor = MagicMock()
        workTest.parseGovDoc = MagicMock()

        workTest.buildWork()
        self.assertIsInstance(workTest.work, WorkRecord)
        self.assertEqual(workTest.work.title, 'Work Test')

    def test_build_instance(self):
        testInstanceRow = {
            'title': 'Instance Test',
            'language': 'en',
            'copyright_date': '2019',
            'publisher_pub_date': 'New York [2019]',
            'pub_place': 'nyu',
            'description': 'testing'
        }
        instanceTest = HathiRecord(testInstanceRow)
        instanceTest.parseIdentifiers = MagicMock()
        instanceTest.parsePubInfo = MagicMock()
        instanceTest.parsePubPlace = MagicMock()

        instanceTest.buildInstance({})
        self.assertIsInstance(instanceTest.instance, InstanceRecord)
        self.assertEqual(instanceTest.instance.language, 'en')
        self.assertEqual(instanceTest.instance.title, 'Instance Test')

    def test_build_item(self):
        testItemRow = {
            'htid': 'test.00000',
            'source': 'nypl',
            'responsible_entity': 'nypl',
            'digitization_entity': 'ia',
        }
        itemTest = HathiRecord(testItemRow)
        itemTest.buildItem()
        self.assertIsInstance(itemTest.item, Format)
        self.assertEqual(itemTest.item.source, 'hathitrust')

    def test_create_rights(self):
        testRightsRow = {
            'htid': 'test.000000',
            'rights': 'pd',
            'rights_statement': 'ipma',
            'rights_determination_date': '2019',
            'copyright_date': '1990'
        }

        rightsTest = HathiRecord(testRightsRow)
        rightsTest.createRights()
        self.assertIsInstance(rightsTest.rights, Rights)
        self.assertEqual(rightsTest.rights.license, 'public_domain')

    def test_parse_identifers(self):
        idenRow = {
            'tests': '1,2,3'
        }
        idenTest = HathiRecord(idenRow)
        idenTest.parseIdentifiers(idenTest.work, 'test', 'tests')
        self.assertIsInstance(idenTest.work.identifiers[0], Identifier)
        self.assertEqual(idenTest.work.identifiers[2].identifier, '3')

    def test_parse_bad_identifiers(self):
        badRow = {
            'badTests': '1,2,3'
        }
        badTest = HathiRecord(badRow)
        badTest.parseIdentifiers(badTest.work, 'test', 'tests')
        self.assertEqual(len(badTest.work.identifiers), 0)

    def test_parse_author(self):
        authorTest = HathiRecord({})
        authorTest.parseAuthor('Tester, Test')
        self.assertIsInstance(authorTest.work.agents[0], Agent)
        self.assertEqual(authorTest.work.agents[0].name, 'Tester, Test')
        self.assertEqual(len(authorTest.work.agents[0].dates), 0)

    def test_parse_author_dates(self):
        authorDateTest = HathiRecord({})
        authorDateTest.parseAuthor('Tester, Test, 1900-2000')
        createdAuthor = authorDateTest.work.agents[0]
        self.assertIsInstance(createdAuthor, Agent)
        self.assertEqual(createdAuthor.name, 'Tester, Test')
        self.assertEqual(len(createdAuthor.dates), 2)
        self.assertEqual(createdAuthor.dates[0].date_type, 'birth_date')
        self.assertEqual(createdAuthor.dates[0].display_date, '1900')
        self.assertEqual(createdAuthor.dates[1].date_type, 'death_date')
        self.assertEqual(createdAuthor.dates[1].display_date, '2000')

    def test_parse_author_single_date(self):
        authorSingleDate = HathiRecord({})
        authorSingleDate.parseAuthor('Tester, Test, b. 1900')
        createdAuthor = authorSingleDate.work.agents[0]
        self.assertIsInstance(createdAuthor, Agent)
        self.assertEqual(createdAuthor.name, 'Tester, Test')
        self.assertEqual(len(createdAuthor.dates), 1)
        self.assertEqual(createdAuthor.dates[0].date_type, 'birth_date')
        self.assertEqual(createdAuthor.dates[0].display_date, '1900')

    def test_pub_place_success(self):
        testCodes = {
            'tst': 'test'
        }
        placeRec = HathiRecord({})
        placeRec.parsePubPlace('tst', testCodes)
        self.assertEqual(placeRec.instance.pub_place, 'test')

    def test_pub_place_failure(self):
        testCodes = {
            'tst': 'test'
        }
        placeRec = HathiRecord({})
        placeRec.parsePubPlace('mis', testCodes)
        self.assertEqual(placeRec.instance.pub_place, 'mis')

    def test_pub_info_date(self):
        pubRec = HathiRecord({})
        pubRec.parsePubInfo('Test, [1900?]')
        self.assertEqual(pubRec.instance.agents[0].name, 'Test')
        self.assertEqual(pubRec.instance.dates[0].display_date, '1900?')

    def test_pub_info_no_date(self):
        pubRec = HathiRecord({})
        pubRec.parsePubInfo('Test.')
        self.assertEqual(pubRec.instance.agents[0].name, 'Test.')

    def test_parse_gov_doc(self):
        govRec = HathiRecord({})
        govRec.parseGovDoc('t')
        self.assertEqual(govRec.work.measurements[0].value, 1)

    def test_parse_non_gov_doc(self):
        govRec = HathiRecord({})
        govRec.parseGovDoc(0)
        self.assertEqual(govRec.work.measurements[0].value, 0)
