import os
import time
import json
from multiprocessing import Queue
from elasticsearch.helpers import bulk, BulkIndexError
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import (
    ConnectionError,
    TransportError,
    ConflictError
)
from elasticsearch_dsl import connections
from elasticsearch_dsl.wrappers import Range


from sqlalchemy.orm import configure_mappers

from model.elasticDocs import (
    Language,
    Work,
    Subject,
    Identifier,
    Agent,
    Measurement,
    Instance,
    Link,
    Item,
    AccessReport,
    Rights
)

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

        configure_mappers()

    def createElasticConnection(self):
        host = os.environ['ES_HOST']
        port = os.environ['ES_PORT']
        timeout = int(os.environ['ES_TIMEOUT'])
        logger.info('Creating connection to ElasticSearch')
        try:
            self.client = Elasticsearch(
                hosts=[{'host': host, 'port': port}],
                timeout=timeout
            )
        except ConnectionError:
            raise ESError('Failed to connect to ElasticSearch instance')
        connections.connections._conns['default'] = self.client

    def createIndex(self):
        if self.client.indices.exists(index=self.index) is False:
            logger.info('Initializing ElasticSearch index {}'.format(
                self.index
            ))
            Work.init()
        else:
            logger.info('ElasticSearch index {} already exists'.format(
                self.index
            ))

    def processBatch(self):
        """Process the current batch of updating records. This utilizes the
        elasticsearch-py bulk helper to import records in chunks of the
        provided size. If a record in the batch errors that is reported and
        logged but it does not prevent the other records in the batch from
        being imported.
        """
        try:
            bulk(
                self.client,
                (work.to_dict(True) for work in self.batch),
                chunk_size=50
            )
        except BulkIndexError as err:
            logger.info('One or more records in the chunk failed to import')
            logger.debug(err)
            raise ESError('Not all records processed smoothly, check logs')

    def indexRecord(self, dbRec):
        """Build an ElasticSearch object from the provided postgresql ORM
        object. This builds a single object from the related tables of the 
        db object that can be indexed and searched in ElasticSearch.
        """
        logger.debug('Creating ES record for {}'.format(dbRec))
        
        workData = {
            field: getattr(dbRec, field, None) for field in Work.getFields()
        }

        self.work = Work(meta={'id': dbRec.uuid}, **workData)
        
        for dateType, date in ESConnection._loadDates(dbRec, ['issued', 'created']).items():
            ESConnection._insertDate(self.work, date, dateType)
        
        self.work.alt_titles = [
            altTitle.title
            for altTitle in dbRec.alt_titles
        ]

        self.work.subjects = [
            Subject(
                authority=subject.authority,
                uri=subject.uri,
                subject=subject.subject
            )
            for subject in dbRec.subjects
        ]
        self.work.agents = [
            ESConnection.addAgent(self.work, agentWork)
            for agentWork in list(dbRec.agent_works)
        ]

        self.work.identifiers = [
            ESConnection.addIdentifier(identifier)
            for identifier in dbRec.identifiers
        ]

        self.work.measurements = [
            Measurement(
                quantity=measure.quantity,
                value = measure.value,
                weight = measure.weight,
                taken_at = measure.taken_at
            ) 
            for measure in dbRec.measurements
        ]

        self.work.links = [ESConnection.addLink(link) for link in dbRec.links]

        self.work.language = [
            ESConnection.addLanguage(lang)
            for lang in dbRec.language
        ]

        self.work.instances = [
            ESConnection.addInstance(instance)
            for instance in dbRec.instances
        ]
        logger.debug('{} instances retrieved for {}'.format(len(self.work.instances), self.work.uuid))
        self._process()

    def _process(self):
        self.batch.append(self.work)
        if len(self.batch) >= 100:
            logger.info('Indexing batch of {} work records'.format(len(self.batch)))
            self.processBatch()
            # Empty batch array for next set of records to be indexed
            self.batch = []

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
        linkData = {
            field: getattr(link, field, None) for field in Link.getFields()
        }
        newLink = Link(**linkData)

        linkFlags = json.loads(getattr(link, 'flags', {}))
        for flag, value in linkFlags.items():
            setattr(newLink, flag, value)
        
        return newLink


    @staticmethod
    def addMeasurement(measurement):
        measureData = {
            field: getattr(measurement, field, None) 
            for field in Measurement.getFields()
        }

        return Measurement(**measureData)

    @staticmethod
    def addLanguage(language):
        languageData = {
            field: getattr(language, field, None)
            for field in Language.getFields()
        }
        return Language(**languageData)

    @staticmethod
    def addRights(rights):
        rightsData = {
            field: getattr(rights, field, None) for field in Rights.getFields()
        }
        newRights = Rights(**rightsData)

        dateTypes = ['copyright_date', 'determination_date']
        for dateType, date in ESConnection._loadDates(rights, dateTypes).items():
            ESConnection._insertDate(newRights, date, dateType)
        
        return newRights
    
    @staticmethod
    def addAgent(record, agentRel):
        match = list(filter(
            lambda x: True 
            if agentRel.agent.name == x.name else False, record.agents
        ))
        if len(match) > 0:
            existing = match[0]
            existing.roles.append(agentRel.role)
        else:
            agent = agentRel.agent
            agentData = {
                field: getattr(agent, field, None) 
                for field in Agent.getFields()
            }
            esAgent = Agent(**agentData)

            esAgent.aliases = []
            for alias in agent.aliases:
                esAgent.aliases.append(alias.alias)

            for dateType, date in ESConnection._loadDates(agent, ['birth_date', 'death_date']).items():
                ESConnection._insertDate(esAgent, date, dateType)

            esAgent.roles = [agentRel.role]

            return esAgent
    
    @staticmethod
    def addInstance(instance):
        instanceData = {
            field: getattr(instance, field, None)
            for field in Instance.getFields()
        }
        esInstance = Instance(**instanceData)

        for dateType, date in ESConnection._loadDates(instance, ['pub_date']).items():
            ESConnection._insertDate(esInstance, date, dateType)
        
        #esInstance.identifiers = [
        #    ESConnection.addIdentifier(identifier)
        #    for identifier in instance.identifiers
        #]

        esInstance.agents = [
            ESConnection.addAgent(esInstance, agentInst)
            for agentInst in instance.agent_instances
        ]

        # NOTE: The two relationships are commented out as they are not
        # currently used in the front-end application. But this data may
        # prove to be useful in the future

        #esInstance.links = [
        #    ESConnection.addLink(link)
        #    for link in instance.links
        #]

        #esInstance.measurements = [
        #    ESConnection.addMeasurement(measure)
        #    for measure in instance.measurements
        #]

        esInstance.items = [
            ESConnection.addItem(item) 
            for item in instance.items
        ]

        esInstance.rights = [
            ESConnection.addRights(rights)
            for rights in instance.rights
        ]

        esInstance.language = [
            ESConnection.addLanguage(lang)
            for lang in instance.language
        ]
        
        return esInstance
    
    @staticmethod
    def addItem(item):
        itemData = {
            field: getattr(item, field, None) for field in Item.getFields()
        }
        esItem = Item(**itemData)

        esItem.identifiers = [
            ESConnection.addIdentifier(identifier)
            for identifier in item.identifiers
        ]
        
        #esItem.agents = [
        #    ESConnection.addAgent(esItem, agentItem)
        #    for agentItem in item.agent_items
        #]
        
        esItem.links = [
            ESConnection.addLink(link)
            for link in item.links
        ]

        for link in esItem.links:
            link.setLabel(esItem.source, esItem.identifiers[0].identifier)
        
        # NOTE: Similar to Instances above, these sections are not in use and
        # are being temporarily removed

        #esItem.measurements = [
        #    ESConnection.addMeasurement(measurement)
        #    for measurement in item.measurements
        #]
        
        #esItem.reports = [
        #    ESConnection.addReport(report)
        #    for report in item.access_reports
        #]

        #esItem.rights = [
        #    ESConnection.addRights(rights)
        #    for rights in item.rights
        #]

        return esItem
    
    @staticmethod
    def addReport(report):
        reportData = {
            field: getattr(report, field, None)
            for field in AccessReport.getFields()
        }
        esReport = AccessReport(**reportData)

        esReport.measurements = [
            ESConnection.addMeasurement(measure)
            for measure in report.measurements
        ]
        
        return esReport.to_dict(True)
    
    @staticmethod
    def _loadDates(record, fields):
        retDates = {}
        for date in record.dates:
            if date.date_type in fields:
                retDates[date.date_type] = {
                    'range': date.date_range,
                    'display': date.display_date
                }
        return retDates

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
