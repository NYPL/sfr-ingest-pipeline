import unittest
from unittest.mock import patch, mock_open, MagicMock, call

from service import handler, loadLocalCSV, fetchHathiCSV, fileParser, rowParser, processChunk, generateChunks
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

    @patch('service.fetchHathiCSV', return_value=['row1', 'row2'])
    @patch('service.fileParser', return_value=True)
    def test_handler_empty(self, mock_file, mock_fetch):
        testRec = {
            'source': 'Kinesis',
            'Records': [{'some': 'record'}]
        }
        resp = handler(testRec, None)
        mock_fetch.assert_called_once()
        self.assertTrue(resp)

    def test_local_csv_success(self):
        mOpen = mock_open(read_data='id1\tr1.2\tpd\nid2\tr2.2\tpd\n')
        mOpen.return_value.__iter__ = lambda self: self
        mOpen.return_value.__next__ = lambda self: next(iter(self.readline, ''))
        with patch('service.open', mOpen, create=True) as mCSV:
            rows = loadLocalCSV('localFile')
            mCSV.assert_called_once_with('localFile', newline='')
            self.assertEqual(rows[0][0], 'id1')

    def test_local_csv_header(self):
        mOpen = mock_open(read_data='htid\tt1\tt2\nid1\tr1.2\tpd\nid2\tr2.2\tpd\n')
        mOpen.return_value.__iter__ = lambda self: self
        mOpen.return_value.__next__ = lambda self: next(iter(self.readline, ''))
        with patch('service.open', mOpen, create=True) as mCSV:
            rows = loadLocalCSV('localFile')
            mCSV.assert_called_once_with('localFile', newline='')
            self.assertEqual(rows[0][0], 'id1')

    def test_local_csv_missing(self):
        with self.assertRaises(ProcessingError):
            loadLocalCSV('localFile')

    @patch.dict('os.environ', {'HATHI_DATAFILES': 'datafile_url'})
    @patch('service.gzip.open')
    def test_fetch_hathi(self, mock_gzip):
        mock_tsv = mock_open()
        with patch('service.requests') as mock_request:
            with patch('service.open', mock_tsv, create=True):
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = [{
                    'created': '2019-01-01T12:00:00-0',
                    'url': 'hathitrust.org/test/file.txt.gz',
                    'full': False
                }]
                mock_resp.content = 'test_content'
                mock_request.get.return_value = mock_resp

                fetchHathiCSV()

                mock_request.get.assert_has_calls([
                    call('datafile_url'),
                    call().json(),
                    call('hathitrust.org/test/file.txt.gz')
                ])
                mock_gzip.assert_called_once()
                


    @patch('service.loadCountryCodes', return_value={})
    @patch('service.Process')
    @patch('service.Pipe')
    def test_file_parser(self, mock_pipe, mock_process, mock_codes):
        testRows = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        mock_parent = MagicMock()
        mock_parent.recv.return_value = ['success', 'success']
        mock_child = MagicMock()
        mock_pipe.return_value = (mock_parent, mock_child)
        res = fileParser(testRows, ['test'])
        self.assertEqual(len(res), 8)
        self.assertEqual(res[7], 'success')

    def test_chunk_parser(self):
        returnValues = [
            ('success', 'htid1'),
            ProcessingError('TestError', 'sampe'),
            ('success', 'htid2')
        ]

        mock_conn = MagicMock()

        with patch('service.rowParser', side_effect=returnValues) as mock_row:
            processChunk(
                [['row1'], ['row2'], ['row3']],
                ['htid'],
                {},
                mock_conn
            )
            mock_row.assert_any_call(['row3'], ['htid'], {})
            mock_row.assert_any_call(['row2'], ['htid'], {})
            mock_row.assert_any_call(['row1'], ['htid'], {})
    
    def test_yield_chunks(self):
        testRows = ['row1', 'row2', 'row3', 'row4', 'row5', 'row6']
        for chunk in generateChunks(testRows, 2):
            self.assertEqual(len(chunk), 2)

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
