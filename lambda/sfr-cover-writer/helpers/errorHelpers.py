class BaseError(Exception):
    def __init__(self, message):
        self.message = message


class NoRecordsReceived(BaseError):
    def __init__(self, message, invocation):
        super().__init__(message)
        self.invocation = invocation


class InvalidExecutionType(BaseError):
    pass


class DataError(BaseError):
    pass


class OutputError(BaseError):
    pass


class InvalidParameter(BaseError):
    pass


class URLFetchError(BaseError):
    def __init__(self, message, status, url):
        super().__init__(message)
        self.status = status
        self.url = url
