import pytest

from lib.s3 import s3Client


class TestS3Client:
    @pytest.fixture
    def testClient(self, mocker):
        mocker.patch('lib.s3.createAWSClient')
        mocker.patch('lib.s3.createLog')
        return s3Client('test/123_456.epub')

    def test_s3Client_init(self, testClient):
        assert testClient.key == 'test/123_456.epub'
        assert testClient.bucket == 'sfr-instance-covers'

    def test_s3Client_checkForFile_found(self, mocker, testClient):
        mocker.patch.object(s3Client, 'returnS3URL', return_value=True)
        testFile = testClient.checkForFile()
        assert testFile is True

    def test_s3Client_storeNewFile_success(self, mocker, testClient):
        mocker.patch.object(s3Client, 'returnS3URL', return_value=True)
        mocker.patch('lib.s3.BytesIO')()
        newURL = testClient.storeNewFile('file_contents', 'testMime')
        assert newURL is True

    def test_returnS3URL(self, testClient):
        outURL = testClient.returnS3URL()
        assert (
            outURL == 'sfr-instance-covers.s3.amazonaws.com/test/123_456.epub'
        )
