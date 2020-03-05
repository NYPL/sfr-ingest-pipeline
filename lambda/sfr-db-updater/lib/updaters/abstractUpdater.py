from abc import ABC, abstractmethod, abstractproperty


class AbstractUpdater(ABC):
    @abstractmethod
    def __init__(self, record, session, kinesisMsgs, sqsMsgs):
        self.session = session
        self.kinesisMsgs = kinesisMsgs
        self.sqsMsgs = sqsMsgs
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
        pass
