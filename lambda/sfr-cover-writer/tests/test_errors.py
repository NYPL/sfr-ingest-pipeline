from helpers.errorHelpers import (
    NoRecordsReceived,
    InvalidExecutionType,
    DataError,
    OutputError,
    InvalidParameter,
    URLFetchError
)


class TestErrors:
    def test_NoRecordsReceived(self):
        testNoRecs = NoRecordsReceived('testMessage', 'testInvocation')
        assert testNoRecs.message == 'testMessage'
        assert testNoRecs.invocation == 'testInvocation'

    def test_InvalidExecutionType(self):
        testInvalidExec = InvalidExecutionType('testMessage')
        assert testInvalidExec.message == 'testMessage'

    def test_DataError(self):
        testDataError = DataError('testMessage')
        assert testDataError.message == 'testMessage'

    def test_OutputError(self):
        testOutputError = OutputError('testMessage')
        assert testOutputError.message == 'testMessage'

    def test_InvalidParameter(self):
        testInvalidParam = InvalidParameter('testMessage')
        assert testInvalidParam.message == 'testMessage'

    def test_URLFetchError(self):
        testURLFetch = URLFetchError('testMessage', 'testStatus', 'testURL')
        assert testURLFetch.message == 'testMessage'
        assert testURLFetch.status == 'testStatus'
        assert testURLFetch.url == 'testURL'
