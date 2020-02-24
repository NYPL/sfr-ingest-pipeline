from helpers.errorHelpers import DataError
from .kMeansModel import KModel
from sfrCore import Work, Edition, Instance
from helpers.logHelpers import createLog

class ClusterManager:
    def __init__(self, record, dbManager):
        self.dbManager = dbManager
        self.parseMessage(record)
        self.logger = createLog('clusterManager')
    
    def parseMessage(self, record):
        self.idType = record.get('type', 'uuid')
        self.identifier = record.get('identifier', None)
        if self.identifier is None:
            self.logger.error('Missing identifier from SQS message')
            raise DataError('Missing identifier for invocation')
    
    def clusterInstances(self):
        session = self.dbManager.createSession()
        self.work = self.fetchWork(session)
        self.logger.info('Creating editions for {}'.format(self.work))

        if len(self.work.instances) < 1:
            raise DataError('Work Record has no attached instance Records')

        mlModel = KModel(self.work.instances)
        mlModel.createDF()
        session.close()
        mlModel.generateClusters()
        self.editions = mlModel.parseEditions()
    
    def deleteExistingEditions(self):
        session = self.dbManager.createSession()
        session.add(self.work)
        self.logger.info('Deleting previous editions for {}'.format(self.work))
        for ed in self.work.editions:
            self.logger.debug('Deleting edition {}'.format(ed))
            session.delete(ed)
        session.commit()
        session.close()

    def storeEditions(self):
        self.logger.debug('Adding new editions to session')
        session = self.dbManager.createSession()
        session.add(self.work)
        session.add_all([
            self.createEdition(session, ed)
            for ed in self.editions
        ])
        session.commit()
        session.close()
    
    def createEdition(self, session, edition):
        self.logger.info('Creating edition for {}'.format(self.work))
        merged = self.mergeInstances(edition)
        self.logger.debug('Merged edition for {}|{}'.format(
            merged.get('pubPlace', ''),
            merged.get('pubDate', '')
        ))
        return Edition.createEdition(
            merged,
            self.work,
            self.fetchInstances(session, merged.pop('rowIDs'))
        )

    def mergeInstances(self, edition):
        out = {'rowIDs': []}
        for inst in edition[1]:
            self.logger.debug('Merging instance with data {}|{}|{}|{}'.format(
                inst['rowID'],
                inst['pubPlace'],
                inst['pubDate'],
                inst['publisher']
            ))
            rowID = inst.pop('rowID')
            inst.pop('publisher')
            cleanInst = {
                key: value for key, value in inst.items()
                if value is not None if value != ''
            }
            out = {**out, **cleanInst}
            out['rowIDs'].append(rowID)
        
        out['edition_statement'] = out.pop('edition', None)
        if int(edition[0]) != 0:
            out['pubDate'] = '[{}-01-01,{}-12-31]'.format(
                int(edition[0]), int(edition[0])
            )
        else:
            out['pubDate'] = None

        return out

    def fetchWork(self, session):
        if self.idType == 'uuid':
            self.logger.debug('Fetching Work by UUID {}'.format(
                self.identifier
            ))
            return Work.getByUUID(session, self.identifier)
        else:
            identifierDict = {
                'type': self.idType,
                'identifier': self.identifier
            }
            self.logger.debug('Fetching Work by {} {}'.format(
                self.idType,
                self.identifier
            ))
            return Work.lookupWork(session, [identifierDict])
    
    def fetchInstances(self, session, instIDs):
        self.logger.debug('Fetching instances for work {}'.format(self.work))
        return session.query(Instance)\
            .filter(Instance.id.in_([int(i) for i in instIDs])).all()