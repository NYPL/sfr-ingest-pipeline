class InvalidExecutionType(Exception):
    def __init__(self, message):
        self.message = message


class VIAFError(Exception):
    def __init__(self, message):
        self.message = message
