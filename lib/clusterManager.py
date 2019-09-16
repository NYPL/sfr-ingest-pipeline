from helpers.errorHelpers import DataError
from .kMeansModel import KModel
from sfrCore import Work, Edition, Instance
from helpers.logHelpers import createLog

class ClusterManager:
    def __init__(self, record, session):
        self.session = session
        self.parseMessage(record)
        self.logger = createLog('clusterManager')
    
    def parseMessage(self, record):
        self.idType = record.get('type', 'uuid')
        self.identifier = record.get('identifier', None)
        if self.identifier is None:
            self.logger.error('Missing identifier from SQS message')
            raise DataError('Missing identifier for invocation')
    
    def clusterInstances(self):
        self.work = self.fetchWork()
        self.logger.info('Creating editions for {}'.format(self.work))

        mlModel = KModel(self.work.instances)
        mlModel.createDF()
        mlModel.generateClusters()
        self.editions = mlModel.parseEditions()
    
    def deleteExistingEditions(self):
        self.logger.info('Deleting previous editions for {}'.format(self.work))
        for ed in self.work.editions:
            self.logger.debug('Deleting edition {}'.format(ed))
            print(ed)
            self.session.delete(ed)

    def storeEditions(self):
        self.logger.debug('Adding new editions to session')
        self.session.add_all([
            self.createEdition(ed)
            for ed in self.editions
        ])
    
    def createEdition(self, edition):
        self.logger.info('Creating edition for {}'.format(self.work))
        merged = self.mergeInstances(edition)
        self.logger.debug('Merged edition for {}|{}'.format(
            merged.get('pubPlace', ''),
            merged.get('pubDate', '')
        ))
        return Edition.createEdition(
            merged,
            self.work,
            self.fetchInstances(merged.pop('rowIDs'))
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

    def fetchWork(self):
        if self.idType == 'uuid':
            self.logger.debug('Fetching Work by UUID {}'.format(
                self.identifier
            ))
            return Work.getByUUID(self.session, self.identifier)
        else:
            identifierDict = {
                'type': self.idType,
                'identifier': self.identifier
            }
            self.logger.debug('Fetching Work by {} {}'.format(
                self.idType,
                self.identifier
            ))
            return Work.lookupWork(self.session, [identifierDict])
    
    def fetchInstances(self, instIDs):
        self.logger.debug('Fetching instances for work {}'.format(self.work))
        return self.session.query(Instance)\
            .filter(Instance.id.in_([int(i) for i in instIDs])).all()