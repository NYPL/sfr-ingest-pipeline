import os
import time
from elasticsearch.helpers import bulk, BulkIndexError
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, TransportError, ConflictError
from elasticsearch_dsl import connections
from elasticsearch_dsl.wrappers import Range

from model.elasticDocs import Work, Subject, Identifier, Agent, Measurement, Instance, Link, Item, AccessReport

from helpers.logHelpers import createLog
from helpers.errorHelpers import ESError

logger = createLog('es_manager')

class ESConnection():
    def __init__(self):
        self.index = os.environ['ES_INDEX']
        self.client = None
        self.work = None
        self.tries = 0
        self.batch = []

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

    def processBatch(self):
        try:
            bulk(self.client, (work.to_dict(True) for work in self.batch), chunk_size=50)
        except BulkIndexError as err:
            logger.debug(err)

    def indexRecord(self, dbRec):
        logger.debug('Indexing record {}'.format(dbRec))
        
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
        self.work.alt_titles = [altTitle.title for altTitle in dbRec.alt_titles]
        self.work.subjects = [Subject(authority=subject.authority, uri=subject.uri, subject=subject.subject) for subject in dbRec.subjects]
        self.work.agents = [ESConnection.addAgent(self.work, agent) for agent in dbRec.agents]
        self.work.identifiers = [ESConnection.addIdentifier(identifier) for identifier in dbRec.identifiers]
        self.work.measurements = [Measurement(quantity=measure.quantity,value = measure.value, weight = measure.weight, taken_at = measure.taken_at) for measure in dbRec.measurements]
        self.work.links = [ESConnection.addLink(link) for link in dbRec.links]
        self.work.instances = [ESConnection.addInstance(instance) for instance in dbRec.instances]
        
        self.batch.append(self.work)

    @staticmethod
    def addIdentifier(identifier):
        idType = identifier.type
        if idType is None:
            idType = 'generic' 
        idRec = getattr(identifier, idType)[0]
        value = getattr(idRec, 'value')
        
        return Identifier(
            id_type=idType,
            identifier=value
        )
    
    @staticmethod
    def addLink(link):
        newLink = Link()
        for field in dir(link):
            setattr(newLink, field, getattr(link, field, None))

        return newLink

    @staticmethod
    def addMeasurement(measurement):
        newMeasure = Measurement()
        for field in dir(measurement):
            setattr(newMeasure, field, getattr(measurement, field, None))
        
        return newMeasure
    
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
                if date['range'] is None:
                    continue
                dateRange = Range(
                    gte=date['range'].lower,
                    lte=date['range'].upper
                )
                setattr(esAgent, dateType, dateRange)
                setattr(esAgent, dateType + '_display', date['display'])

            esAgent.role = agentRel.role

            return esAgent
    
    @staticmethod
    def addInstance(instance):
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
        esInstance.identifiers = [ESConnection.addIdentifier(identifier) for identifier in instance.identifiers]
        esInstance.agents = [ESConnection.addAgent(esInstance, agent) for agent in instance.agents]
        esInstance.links = [ESConnection.addLink(link) for link in instance.links]
        esInstance.measurements = [ESConnection.addMeasurement(measure) for measure in instance.measurements]
        esInstance.items = [ESConnection.addItem(item) for item in instance.items]
        
        return esInstance
    
    @staticmethod
    def addItem(item):
        esItem = Item()

        for field in dir(item):
            setattr(esItem, field, getattr(item, field, None))
        esItem.identifiers = [ESConnection.addIdentifier(identifier) for identifier in item.identifiers]
        esItem.agents = [ESConnection.addAgent(esItem, agent) for agent in item.agents]
        esItem.links = [ESConnection.addLink(link) for link in item.links]
        esItem.measurements = [ESConnection.addMeasurement(measurement) for measurement in item.measurements]
        esItem.reports = [ESConnection.addReport(report) for report in item.access_reports]

        return esItem
    
    @staticmethod
    def addReport(report):
        esReport = AccessReport()

        for field in dir(report):
            setattr(esReport, field, getattr(report, field, None))
        
        esReport.measurements = [ESConnection.addMeasurement(measure) for measure in report.measurements]
        
        return esReport.to_dict(True)
