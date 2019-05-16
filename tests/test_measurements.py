import unittest
from unittest.mock import patch, MagicMock, call

from sfrCore.model import Measurement

class MeasurementTest(unittest.TestCase):
    def test_measure_repr(self):
        testMeasure = Measurement()
        testMeasure.quantity = 'test'
        testMeasure.value = 0
        self.assertEqual(str(testMeasure), '<Measurement(quantity=test, value=0)>')
    
    @patch.object(Measurement, 'lookupMeasure', return_value=None)
    @patch.object(Measurement, 'insert', return_value='newMeasure')
    def test_measure_updateInsert_insert(self, mock_insert, mock_lookup):
        fakeMeasure = {'quantity': 'test'}
        testMeasure = Measurement.updateOrInsert('session', fakeMeasure, 'testing', 1)
        self.assertEqual(testMeasure, 'newMeasure')
    
    @patch.object(Measurement, 'lookupMeasure')
    def test_measure_updateInsert_update(self, mock_lookup):
        fakeMeasure = {'quantity': 'test'}
        mock_existing = MagicMock()
        mock_lookup.return_value = mock_existing
        testMeasure = Measurement.updateOrInsert('session', fakeMeasure, 'testing', 1)
        self.assertEqual(testMeasure, mock_existing)
    
    def test_measure_insert(self):
        testMeasure = Measurement.insert({'quantity': 'test'})
        self.assertIsInstance(testMeasure, Measurement)
        self.assertEqual(testMeasure.quantity, 'test')

    def test_measure_update(self):
        testMeasure = Measurement()
        testMeasure.value = 0

        testMeasure.update({'value': 1})
        self.assertEqual(testMeasure.value, 1)
    
    def test_measure_lookup_success(self):
        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_model.__tablename__ = 'testing'
        mock_session.query()\
            .join()\
            .filter().filter().filter()\
            .one_or_none.return_value = 'testMeasure'
        testMeasure = Measurement.lookupMeasure(mock_session, {'quantity': 'test', 'source_id': '1'}, mock_model, 1)
        self.assertEqual(testMeasure, 'testMeasure')