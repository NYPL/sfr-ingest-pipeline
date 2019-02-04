import os
import time
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, TransportError, ConflictError
from elasticsearch_dsl import connections
from elasticsearch_dsl.wrappers import Range

from model.elasticDocs import Work, Subject, Identifier, Agent, Measurement, Instance, Link, Item, AccessReport, Rights

from helpers.logHelpers import createLog
from helpers.errorHelpers import ESError

logger = createLog('es_manager')

class ESConnection():
    def __init__(self):
        self.index = os.environ['ES_INDEX']
        self.client = None
        self.work = None
        self.tries = 0

        self.createElasticConnection()
        self.createIndex()

    def createElasticConnection(self):
        host = os.environ['ES_HOST']
        port = os.environ['ES_PORT']
        timeout = int(os.environ['ES_TIMEOUT'])
        logger.info('Creating connection to ElasticSearch')
        try:
            self.client = Elasticsearch(hosts=[{'host': host, 'port': port}], timeout=timeout)
        except ConnectionError:
            raise ESError('Failed to connect to ElasticSearch instance')
        connections.connections._conns['default'] = self.client

    def createIndex(self):
        if self.client.indices.exists(index=self.index) is False:
            logger.info('Initializing ElasticSearch index {}'.format(self.index))
            Work.init()
        else:
            logger.info('ElasticSearch index {} already exists'.format(self.index))

    def indexRecord(self, dbRec):
        logger.debug('Indexing record {}'.format(dbRec))
        try:
            self.work = Work.get(id=dbRec.uuid)
            logger.debug('Found existing record for {}'.format(dbRec.uuid))
        except TransportError:
            logger.debug('Existing record not found, create new document')
            self.work = Work(meta={'id': dbRec.uuid})

        for field in dir(dbRec):
            setattr(self.work, field, getattr(dbRec, field, None))
        
        for dateType, date in dbRec.loadDates(['issued', 'created']).items():
            if date['range'] is None:
                continue
            dateRange = Range(
                gte=date['range'].lower,
                lte=date['range'].upper
            )
            setattr(self.work, dateType, dateRange)
            setattr(self.work, dateType + '_display', date['display'])
        
        self.work.alt_titles = []
        for altTitle in dbRec.alt_titles:
            self.work.alt_titles.append(altTitle.title)
        
        self.work.subjects = []
        for subject in dbRec.subjects:
            self.work.subjects.append(Subject(
                authority=subject.authority,
                uri=subject.uri,
                subject=subject.subject
            ))
        
        self.work.agents = []
        for agent in dbRec.agents:
            ESConnection.addAgent(self.work, agent)
        
        self.work.identifiers = []
        for identifier in dbRec.identifiers:
            ESConnection.addIdentifier(self.work, identifier)

        self.work.measurements = []
        for measure in dbRec.measurements:
            self.work.measurements.append(Measurement(
                quantity=measure.quantity,
                value = measure.value,
                weight = measure.weight,
                taken_at = measure.taken_at
            ))
        
        self.work.links = []
        for link in dbRec.links:
            ESConnection.addLink(self.work, link)
        
        self.work.rights = []
        for rightsStmt in dbRec.rights:
            ESConnection.addRights(self.work, rightsStmt)
        
        self.work.instances = []
        for instance in dbRec.instances:
            ESConnection.addInstance(self.work, instance)
        
        try:
            self.work.save()
        except ConflictError as err:
            logger.warning('Found more recent version of document in index (greater than {}'.format(self.work.meta.version))
            logger.debug(err)
            if self.tries < 3:
                logger.info('Backing off, then retrying to index')
                time.sleep(3)
                self.indexRecord(dbRec)
                self.tries += 1
            else:
                logger.debug('Too many tries attempted, abandoning version {} of record {}'.format(self.work.meta.version, self.work.uuid))

    @staticmethod
    def addIdentifier(record, identifier):
        idType = identifier.type
        if idType is None:
            idType = 'generic' 
        idRec = getattr(identifier, idType)[0]
        value = getattr(idRec, 'value')
        record.identifiers.append(Identifier(
            id_type=idType,
            identifier=value
        ))
    
    @staticmethod
    def addLink(record, link):
        newLink = Link()
        for field in dir(link):
            setattr(newLink, field, getattr(link, field, None))

        record.links.append(newLink)

    @staticmethod
    def addMeasurement(record, measurement):
        newMeasure = Measurement()
        for field in dir(measurement):
            setattr(newMeasure, field, getattr(measurement, field, None))
        
        record.measurements.append(newMeasure)
    
    @staticmethod
    def addAgent(record, agentRel):
        match = list(filter(lambda x: True if agentRel.agent.name == x.name else False, record.agents))
        if len(match) > 0:
            existing = match[0]
            existing.aliases.append(agentRel.role)
        else:
            esAgent = Agent()
            agent = agentRel.agent
            for field in dir(agent):
                setattr(esAgent, field, getattr(agent, field, None))
            
            esAgent.aliases = []
            for alias in agent.aliases:
                esAgent.aliases.append(alias.alias)
            
            for dateType, date in agent.loadDates(['birth_date', 'death_date']).items():
                ESConnection._insertDate(esAgent, date, dateType)


            esAgent.roles = [agentRel.role]
            record.agents.append(esAgent)
    
    @staticmethod
    def addRights(record, rights):
        esRights = Rights()
        for field in dir(rights):
            setattr(esRights, field, getattr(rights, field, None))
        
        for dateType, date in rights.loadDates(['copyright_date', 'determination_date']).items():
            ESConnection._insertDate(esRights, date, dateType)

        record.rights.append(esRights)

    @staticmethod
    def addInstance(record, instance):
        esInstance = Instance()
        for field in dir(instance):
            setattr(esInstance, field, getattr(instance, field, None))
        
        for dateType, date in instance.loadDates(['pub_date', 'copyright_date']).items():
            if date['range'] is None:
                continue
            dateRange = Range(
                gte=date['range'].lower,
                lte=date['range'].upper
            )
            setattr(esInstance, dateType, dateRange)
            setattr(esInstance, dateType + '_display', date['display'])

        esInstance.identifiers = []
        for identifier in instance.identifiers:
            ESConnection.addIdentifier(esInstance, identifier)
        
        esInstance.agents = []
        for agent in instance.agents:
            ESConnection.addAgent(esInstance, agent)
        
        esInstance.links = []
        for link in instance.links:
            ESConnection.addLink(esInstance, link)
        
        esInstance.measurements = []
        for measure in instance.measurements:
            ESConnection.addMeasurement(esInstance, measure)
        
        esInstance.items = []
        for item in instance.items:
            ESConnection.addItem(esInstance, item)

        record.instances.append(esInstance)
    
    @staticmethod
    def addItem(record, item):
        esItem = Item()

        for field in dir(item):
            setattr(esItem, field, getattr(item, field, None))
        
        for identifier in item.identifiers:
            ESConnection.addIdentifier(esItem, identifier)
        
        for agent in item.agents:
            ESConnection.addAgent(esItem, agent)
        
        for link in item.links:
            ESConnection.addLink(esItem, link)
        
        for measure in item.measurements:
            ESConnection.addMeasurement(esItem, measure)
        
        for report in item.access_reports:
            ESConnection.addReport(esItem, report)
        
        record.items.append(esItem)
    
    @staticmethod
    def addReport(record, report):
        esReport = AccessReport()

        for field in dir(report):
            setattr(esReport, field, getattr(report, field, None))
        
        for measure in report.measurements:
            ESConnection.addMeasurement(esReport, measure)
        
        record.access_reports.append(esReport)
    
    @staticmethod
    def _insertDate(record, date, dateType):
        if date['range'] is None:
                return
        dateRange = Range(
            gte=date['range'].lower,
            lte=date['range'].upper
        )
        setattr(record, dateType, dateRange)
        setattr(record, dateType + '_display', date['display'])
