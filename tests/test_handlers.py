import unittest
from unittest.mock import patch, mock_open

from service import handler, loadLocalCSV, fetchHathiCSV, fileParser, rowParser
from helpers.errorHelpers import ProcessingError, DataError, KinesisError


class TestHandler(unittest.TestCase):

    @patch('service.loadLocalCSV', return_value=['row1', 'row2'])
    @patch('service.fileParser', return_value=True)
    def test_handler_local(self, mock_parser, mock_load):
        testRec = {
            'source': 'local.file',
            'localFile': 'test.csv'
        }
        resp = handler(testRec, None)
        mock_load.assert_called_once()
        mock_parser.assert_called_once()
        self.assertTrue(resp)

    @patch('service.fetchHathiCSV', return_value=['row1', 'row2'])
    @patch('service.fileParser', return_value=True)
    def test_handler_scheduled(self, mock_parser, mock_fetch):
        testRec = {
            'source': 'Kinesis',
            'Records': [{'some': 'record'}]
        }

        resp = handler(testRec, None)
        mock_fetch.assert_called_once()
        mock_parser.assert_called_once()
        self.assertTrue(resp)

    @patch('service.fetchHathiCSV', return_value=None)
    def test_handler_empty(self, mock_fetch):
        testRec = {
            'source': 'Kinesis',
            'Records': [{'some': 'record'}]
        }
        resp = handler(testRec, None)
        mock_fetch.assert_called_once()
        self.assertEqual(resp[0][0], 'empty')

    def test_local_csv_success(self):
        mOpen = mock_open(read_data='row1\nrow2\n')
        mOpen.return_value.__iter__ = lambda self: self
        mOpen.return_value.__next__ = lambda self: next(iter(self.readline, ''))
        with patch('service.open', mOpen, create=True) as mCSV:
            rows = loadLocalCSV('localFile')
            mCSV.assert_called_once_with('localFile', newline='')
            self.assertEqual(rows[0][0], 'row1')

    def test_local_csv_header(self):
        mOpen = mock_open(read_data='htid\nrow1\nrow2\n')
        mOpen.return_value.__iter__ = lambda self: self
        mOpen.return_value.__next__ = lambda self: next(iter(self.readline, ''))
        with patch('service.open', mOpen, create=True) as mCSV:
            rows = loadLocalCSV('localFile')
            mCSV.assert_called_once_with('localFile', newline='')
            self.assertEqual(rows[0][0], 'row1')

    def test_local_csv_missing(self):
        with self.assertRaises(ProcessingError):
            loadLocalCSV('localFile')

    def test_fetch_hathi(self):
        # Placeholder test until method is implemented
        self.assertIsNone(fetchHathiCSV())

    @patch('service.loadCountryCodes', return_value={})
    def test_file_parser(self, mock_codes):
        returnValues = [
            ('success', 'htid1'),
            ProcessingError('TestError', 'sampe'),
            ('success', 'htid2')
        ]
        with patch('service.rowParser', side_effect=returnValues) as mock_row:
            outcomes = fileParser([['row1'], ['row2'], ['row3']], ['htid'])
            mock_row.assert_any_call(['row3'], ['htid'], {})
            mock_row.assert_any_call(['row2'], ['htid'], {})
            mock_row.assert_any_call(['row1'], ['htid'], {})

        self.assertEqual(outcomes[0][0], 'success')
        self.assertEqual(outcomes[1][0], 'failure')

    @patch.dict('os.environ', {'OUTPUT_STREAM': 'test-stream'})
    @patch('service.HathiRecord')
    @patch('service.KinesisOutput')
    def test_row_parse_success(self, mock_kinesis, mock_hathi):
        result = rowParser(['row1'], ['htid'], {})
        self.assertEqual(result[0], 'success')

    @patch('service.HathiRecord')
    def test_row_parse_data_error(self, mock_hathi):
        mock_hathi().buildDataModel.side_effect = DataError('Test Error')
        with self.assertRaises(ProcessingError):
            rowParser(['row1'], ['htid'], {})

    @patch.dict('os.environ', {'OUTPUT_STREAM': 'test-stream'})
    @patch('service.HathiRecord')
    @patch('service.KinesisOutput')
    def test_row_parse_kinesis_error(self, mock_kinesis, mock_hathi):
        mock_kinesis.putRecord.side_effect = KinesisError('Test Error')
        with self.assertRaises(ProcessingError):
            rowParser(['row1'], ['htid'], {})
