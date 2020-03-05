import unittest
from unittest.mock import patch, mock_open, call

from lib.dataModel import DataObject, WorkRecord, Format, Link, Agent, Measurement

class DataModel(unittest.TestCase):

    def test_root_create(self):
        model = DataObject()
        self.assertIsInstance(model, DataObject)

    def test_root_set(self):
        model = DataObject()
        model.test = 'test1'
        model['test2'] = 'test2'
        self.assertEqual(model.test, 'test1')
        self.assertEqual(model.test2, 'test2')

    def test_root_get(self):
        model = DataObject()
        model.test = 'tester'
        self.assertEqual(model.__getitem__('test'), 'tester')

    def test_root_getDict(self):
        model = DataObject()
        model.test = 'tester'
        self.assertEqual(model.getDictValue(), {'test': 'tester'})

    def test_root_createFromDict(self):
        model = DataObject.createFromDict(**{'test': 'tester'})
        self.assertIsInstance(model, DataObject)
        self.assertEqual(model.getDictValue(), {'test': 'tester'})

    def test_work_create(self):
        work = WorkRecord()
        self.assertIsInstance(work, WorkRecord)
        self.assertIsInstance(work, WorkRecord)

    def test_work_addIdentifier(self):
        work = WorkRecord()
        work.addIdentifier(**{'type': 'test', 'identifier': 1})
        self.assertEqual(len(work.identifiers), 1)
        self.assertEqual(work.identifiers[0]['identifier'], 1)

    def test_work_addInstance(self):
        work = WorkRecord()
        work.addInstance(**{'title': 'test', 'language': 'en'})
        self.assertEqual(len(work.instances), 1)
        self.assertEqual(work.instances[0]['title'], 'test')

    def test_work_addSubject(self):
        work = WorkRecord()
        work.addSubject(**{'type': 'fast', 'value': 'test'})
        self.assertEqual(len(work.subjects), 1)
        self.assertEqual(work.subjects[0]['value'], 'test')

    def test_work_addAgent(self):
        work = WorkRecord()
        work.addAgent(**{'name': 'Test, Tester', 'role': 'tester'})
        self.assertEqual(len(work.agents), 1)
        self.assertEqual(work.agents[0]['role'], 'tester')

    def test_work_addMeasurement(self):
        work = WorkRecord()
        work.addMeasurement(**{'quantity': 'test', 'value': 1})
        self.assertEqual(len(work.measurements), 1)
        self.assertEqual(work.measurements[0]['value'], 1)

    def test_format_create(self):
        testFormat = Format('ebook', 'http://test.test', 'now')
        self.assertIsInstance(testFormat, Format)
        self.assertEqual(testFormat.content_type, 'ebook')

    def test_format_create_with_link(self):
        testFormat = Format('ebook', Link('testing'), 'now')
        self.assertIsInstance(testFormat, Format)
        self.assertEqual(testFormat.links[0].url, 'testing')

    def test_format_setLink(self):
        testFormat = Format('ebook', 'test', 'now')
        testFlags = {'local': False, 'download': False, 'ebook': True}
        testFormat.setLink(**{'url': 'https://hello.hello', 'mediaType': 'text/html', 'flags': testFlags})
        self.assertTrue(testFormat.links[0].flags['ebook'])

    def test_agent_non_matching(self):
        new = [Agent('Test, Tester', 'tester')]
        existing = [Agent('Other, Agent', 'user')]
        merged = Agent.checkForMatches(new, existing)
        self.assertEqual(len(merged), 2)

    def test_agent_merging(self):
        new = [Agent('Test, Tester', 'tester', ['Bad, Tester'])]
        existing = [Agent('Testing, Tester', 'user', ['Tester, Bad'])]
        merged = Agent.checkForMatches(new, existing)
        self.assertEqual(len(merged), 1)

    def test_get_measurement_value(self):
        measure = Measurement('test', 2, 1, 'now')
        value = Measurement.getValueForMeasurement([measure], 'test')
        self.assertEqual(value, 2)
