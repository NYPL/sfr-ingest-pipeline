
class NoRecordsReceived(Exception):
    def __init__(self, message, invocation):
        self.message = message
        self.invocation = invocation


class InvalidExecutionType(Exception):
    def __init__(self, message):
        self.message = message


class ProcessingError(Exception):
    def __init__(self, source, message):
        self.source = source
        self.message = message


class DataError(Exception):
    def __init__(self, message):
        self.message = message


class KinesisError(Exception):
    def __init__(self, message):
        self.message = message


class URLFetchError(Exception):
    def __init__(self, message, status, url):
        self.message = message
        self.status = status
        self.url = url
