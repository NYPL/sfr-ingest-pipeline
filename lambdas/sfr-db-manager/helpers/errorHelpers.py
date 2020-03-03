
class NoRecordsReceived(Exception):
    def __init__(self, message, invocation):
        self.message = message
        self.invocation = invocation


class InvalidExecutionType(Exception):
    def __init__(self, message):
        self.message = message


class OutputError(Exception):
    def __init__(self, message):
        self.message = message


class DBError(Exception):
    def __init__(self, table, message):
        self.table = table
        self.message = message


class DataError(Exception):
    def __init__(self, message):
        self.message = message
