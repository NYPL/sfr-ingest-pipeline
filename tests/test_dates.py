import unittest
from unittest.mock import patch
from collections import namedtuple

from model.date import DateField

TestDate = namedtuple('TestDate', ['id', 'display_date', 'date_range', 'date_type'])


class TestDates(unittest.TestCase):

    @patch('model.date.DateField.parseDate', return_value='[3,4)')
    def test_insert_date(self, mock_parse):
        newDate = {
            'display_date': 'new',
            'date_range': '[3,4)',
            'date_type': 'tester'
        }
        res = DateField.insert(newDate)
        self.assertEqual(res.display_date, 'new')
        self.assertEqual(res.date_range, '[3,4)')
        self.assertEqual(res.date_type, 'tester')

    def test_parse_single_date(self):
        res = DateField.parseDate('2018-01-10')
        self.assertEqual(res, '[2018-01-10,)')

    def test_parse_date_list(self):
        res = DateField.parseDate(['2018-01-10', '2018-01-11'])
        self.assertEqual(res, '[2018-01-10, 2018-01-11)')

    def test_parse_year(self):
        res = DateField.parseDate('2018')
        self.assertEqual(res, '[2018-01-01, 2018-12-31)')

    def test_parse_month(self):
        res = DateField.parseDate('2018-02')
        self.assertEqual(res, '[2018-02-01, 2018-02-28)')

    def test_parse_bad_date(self):
        res = DateField.parseDate('Modnay, Dec 01, 87')
        self.assertEqual(res, None)
