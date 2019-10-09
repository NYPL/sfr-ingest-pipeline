from abc import ABC, abstractmethod, abstractproperty

from helpers.logHelpers import createLog


class AbstractUpdater(ABC):
    @abstractmethod
    def __init__(self, record, session):
        self.session = session
        self.logger = self.createLogger()

    @abstractproperty
    def identifier(self):
        pass

    @abstractmethod
    def lookupRecord(self):
        pass

    @abstractmethod
    def updateRecord(self):
        pass

    @abstractmethod
    def setUpdateTime(self):
        pass

    def createLogger(self):
        return createLog(type(self).__name__)
