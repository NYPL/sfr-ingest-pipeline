class InvalidExecutionType(Exception):
    def __init__(self, message):
        self.message = message


class UnglueError(Exception):
    def __init__(self, status, message):
        self.message = message
        self.status = status
