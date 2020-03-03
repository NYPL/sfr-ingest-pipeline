from abc import ABC, abstractmethod, abstractproperty


class AbstractImporter(ABC):
    @abstractmethod
    def __init__(self, record, session):
        self.session = session
        self.logger = self.createLogger()

    @abstractproperty
    def identifier(self):
        return None

    @abstractmethod
    def lookupRecord(self):
        return None

    @abstractmethod
    def insertRecord(self):
        return None

    @abstractmethod
    def setInsertTime(self):
        pass

    def createLogger(self):
        pass
