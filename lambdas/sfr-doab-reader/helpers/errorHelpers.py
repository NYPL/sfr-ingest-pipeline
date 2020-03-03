
class NoRecordsReceived(Exception):
    def __init__(self, message, invocation):
        self.message = message
        self.invocation = invocation


class InvalidExecutionType(Exception):
    def __init__(self, message):
        self.message = message
    

class OAIFeedError(Exception):
    def __init__(self, message):
        self.message = message


class MARCXMLError(Exception):
    def __init__(self, message):
        self.message = message


class DataError(Exception):
    def __init__(self, message):
        self.message = message


class KinesisError(Exception):
    def __init__(self, message):
        self.message = message