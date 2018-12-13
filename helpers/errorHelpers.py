#
# Custom Error Classes for Python Lambdas
# These define common behavior that can be encountered in AWS/Lambda
# and provide clearer messaging as to the specific issues encountered
#

class NoRecordsReceived(Exception):
    def __init__(self, message, invocation):
        self.message = message
        self.invocation = invocation


class InvalidExecutionType(Exception):
    def __init__(self, message):
        self.message = message


class OCLCError(Exception):
    def __init__(self, message):
        self.message = message


class KinesisError(Exception):
    def __init__(self, message):
        self.message = message
