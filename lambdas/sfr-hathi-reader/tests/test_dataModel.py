import unittest

from lib.dataModel import (
    DataObject,
    WorkRecord,
    InstanceRecord,
    Format,
    Identifier,
    Agent,
    Subject,
    Link,
    Measurement,
    Rights,
    Date
)
from helpers.errorHelpers import DataError


class TestModel(unittest.TestCase):

    # Tests for DataObject base class
    def test_base_create(self):
        testRec = DataObject()
        self.assertIsInstance(testRec, DataObject)

    def test_base_set_get(self):
        testRec = DataObject()
        testRec['hello'] = 'world'
        self.assertEqual(testRec['hello'], 'world')

    def test_base_get_dict(self):
        testRec = DataObject()
        testRec.test = 'tester'
        testRec.count = 1
        outDict = testRec.getDictValue()
        self.assertEqual(outDict['test'], 'tester')
        self.assertEqual(outDict['count'], 1)

    def test_base_dict_create(self):
        with self.assertRaises(DataError):
            DataObject.createFromDict(**{
                'test': 'tester',
                'count': 1
            })

    def test_base_add_identifier(self):
        testRec = DataObject()
        with self.assertRaises(DataError):
            testRec.addClassItem('identifiers', Identifier, **{
                'identifier': 1
            })

    # Tests for WorkRecord object
    def test_work_create(self):
        workTest = WorkRecord()
        self.assertIsInstance(workTest, WorkRecord)

    def test_work_repr(self):
        workTest = WorkRecord()
        workTest.title = 'Test_title'
        self.assertEqual(
            str(workTest),
            '<Work(title=Test_title, primary_id=None)>'
        )

    def test_create_from_dict(self):
        workTest = WorkRecord.createFromDict(**{
            'title': 'A Title',
            'uuid': '0000000-0000-0000-0000-00000000000'
        })
        self.assertIsInstance(workTest, WorkRecord)
        self.assertEqual(workTest.title, 'A Title')

    def test_add_identifier_success(self):
        idenTest = WorkRecord()
        idenTest.addClassItem('identifiers', Identifier, **{
            'identifier': 1
        })
        self.assertEqual(len(idenTest.identifiers), 1)
        self.assertEqual(idenTest.identifiers[0].identifier, 1)

    # Tests for InstanceRecord object
    def test_instance_create(self):
        instanceTest = InstanceRecord(title='Some Title', language='en')
        self.assertIsInstance(instanceTest, InstanceRecord)
        self.assertEqual(instanceTest.title, 'Some Title')
        self.assertEqual(instanceTest.language, 'en')

    def test_instance_repr(self):
        instanceTest = InstanceRecord(title='A Title')
        instanceTest.pub_place = 'New York'
        self.assertEqual(
            str(instanceTest),
            '<Instance(title=A Title, pub_place=New York)>'
        )

    # Tests for Item object
    def test_format_create(self):
        itemTest = Format()
        self.assertIsInstance(itemTest, Format)

    def test_format_create_with_link(self):
        itemTest = Format(link='http://fake.com')
        self.assertIsInstance(itemTest.links[0], Link)
        self.assertEqual(itemTest.links[0].url, 'http://fake.com')

    def test_fromat_create_with_link_object(self):
        linkTest = Link(url='http://fake.com')
        itemTest = Format(link=linkTest)
        self.assertIsInstance(itemTest.links[0], Link)
        self.assertEqual(itemTest.links[0].url, 'http://fake.com')

    def test_item_repr(self):
        itemTest = Format(contentType='text/html', source='test')
        self.assertEqual(str(itemTest), '<Item(type=text/html, source=test)>')

    # Tests for Agent object
    def test_agent_create(self):
        agentTest = Agent()
        self.assertIsInstance(agentTest, Agent)

    def test_agent_create_role(self):
        agentTest = Agent(role='tester')
        self.assertEqual(agentTest.roles, ['tester'])

    def test_agent_create_role_list(self):
        agentTest = Agent(role=['tester'])
        self.assertEqual(agentTest.roles, ['tester'])

    def test_agent_repr(self):
        agentTest = Agent(name='Test, Tester', role='tester')
        self.assertEqual(
            str(agentTest),
            '<Agent(name=Test, Tester, roles=tester)>'
        )

    # Tests for Identifier object
    def test_identifier_create(self):
        idenTest = Identifier()
        self.assertIsInstance(idenTest, Identifier)

    def test_identifier_repr(self):
        idenTest = Identifier(type='test', identifier='1')
        self.assertEqual(str(idenTest), '<Identifier(type=test, id=1)>')

    # Tests for Link object
    def test_link_create(self):
        linkTest = Link()
        self.assertIsInstance(linkTest, Link)

    def test_link_repr(self):
        linkTest = Link(url='test', mediaType='test')
        self.assertEqual(str(linkTest), '<Link(url=test, type=test)>')

    # Tests for Subject object
    def test_subject_create(self):
        subjectTest = Subject()
        self.assertIsInstance(subjectTest, Subject)

    def test_subject_repr(self):
        subjectTest = Subject(subjectType='test', value='subject')
        self.assertEqual(
            str(subjectTest),
            '<Subject(authority=test, subject=subject)>'
        )

    # Tests for Measurement object
    def test_measurement_create(self):
        measureTest = Measurement()
        self.assertIsInstance(measureTest, Measurement)

    def test_measurement_repr(self):
        measureTest = Measurement(quantity='test', value='1')
        self.assertEqual(
            str(measureTest),
            '<Measurement(quantity=test, value=1)>'
        )

    def test_get_measurement_value(self):
        testMeasures = [
            Measurement(quantity='test', value=1),
            Measurement(quantity='test2', value=3)
        ]
        self.assertEqual(
            Measurement.getValueForMeasurement(testMeasures, 'test2'),
            3
        )

    # Tests for Date object
    def test_date_create(self):
        dateTest = Date()
        self.assertIsInstance(dateTest, Date)

    def test_date_repr(self):
        dateTest = Date(displayDate='2019-01-01', dateType='test')
        self.assertEqual(str(dateTest), '<Date(date=2019-01-01, type=test)>')

    # Tests for Rights object
    def test_rights_create(self):
        rightsTest = Rights()
        self.assertIsInstance(rightsTest, Rights)

    def test_rights_repr(self):
        rightsTest = Rights(license='CC0')
        self.assertEqual(str(rightsTest), '<Rights(license=CC0)>')
