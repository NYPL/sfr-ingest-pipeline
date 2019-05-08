
class DBError(Exception):
    def __init__(self, table, message):
        self.table = table
        self.message = message


class DataError(Exception):
    def __init__(self, message):
        self.message = message