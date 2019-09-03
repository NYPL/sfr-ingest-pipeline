import os
import time
import json
from elasticsearch.helpers import bulk, BulkIndexError, streaming_bulk
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import (
    ConnectionError,
    TransportError,
    ConflictError
)
from elasticsearch_dsl import connections
from elasticsearch_dsl.wrappers import Range


from sqlalchemy.orm import configure_mappers

from sfrCore import Work as DBWork

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

from lib.dbManager import retrieveRecords

from helpers.logHelpers import createLog
from helpers.errorHelpers import ESError

logger = createLog('es_manager')

class ESConnection():
    def __init__(self):
        self.index = os.environ['ES_INDEX']
        self.client = None
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
    
    def generateRecords(self, session):
        """Process the current batch of updating records. This utilizes the
        elasticsearch-py bulk helper to import records in chunks of the
        provided size. If a record in the batch errors that is reported and
        logged but it does not prevent the other records in the batch from
        being imported.
        """
        success, failure = 0, 0
        errors = []
        try:
            for status, work in streaming_bulk(self.client, self.process(session)):
                if not status:
                    errors.append(work)
                    failure += 1
                else:
                    success += 1
            
            logger.info('Success {} | Failure: {}'.format(success, failure))
        except BulkIndexError as err:
            logger.info('One or more records in the chunk failed to import')
            logger.debug(err)
            raise ESError('Not all records processed smoothly, check logs')


    def process(self, session):
        for workID in retrieveRecords(session):
            esWork = ESDoc(workID, session)
            esWork.indexWork()
            yield esWork.work.to_dict(True)

class ESDoc():
    def __init__(self, workID, session):
        self.workID = workID[0]
        self.session = session
        self.dbRec = None
        self.work = self.createWork()
    
    def createWork(self):
        self.dbRec = self.session.query(DBWork).get(self.workID)
        logger.debug('Creating ES record for {}'.format(self.dbRec))

        workData = {
            field: getattr(self.dbRec, field, None) for field in Work.getFields()
        }

        return Work(meta={'id': self.dbRec.uuid}, **workData)

    def indexWork(self):
        """Build an ElasticSearch object from the provided postgresql ORM
        object. This builds a single object from the related tables of the 
        db object that can be indexed and searched in ElasticSearch.
        """

        for dateType, date in ESDoc._loadDates(self.dbRec, ['issued', 'created']).items():
            ESDoc._insertDate(self.work, date, dateType)
        
        self.work.alt_titles = [
            altTitle.title
            for altTitle in self.dbRec.alt_titles
        ]

        self.work.subjects = [
            Subject(
                authority=subject.authority,
                uri=subject.uri,
                subject=subject.subject
            )
            for subject in self.dbRec.subjects
        ]
        self.work.agents = [
            ESDoc.addAgent(self.work, agentWork)
            for agentWork in list(self.dbRec.agent_works)
        ]

        self.work.identifiers = [
            ESDoc.addIdentifier(identifier)
            for identifier in self.dbRec.identifiers
        ]

        self.work.measurements = [
            Measurement(
                quantity=measure.quantity,
                value = measure.value,
                weight = measure.weight,
                taken_at = measure.taken_at
            ) 
            for measure in self.dbRec.measurements
        ]

        self.work.links = [ESDoc.addLink(link) for link in self.dbRec.links]

        self.work.language = [
            ESDoc.addLanguage(lang)
            for lang in self.dbRec.language
        ]

        self.work.instances = [
            ESDoc.addInstance(instance)
            for instance in self.dbRec.instances
        ]
        logger.debug('{} instances retrieved for {}'.format(len(self.dbRec.instances), self.work.uuid))

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
        newLink.unique_id = link.id

        linkFlags = getattr(link, 'flags', {})
        if isinstance(linkFlags, str): linkFlags = json.loads(linkFlags)
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
        for dateType, date in ESDoc._loadDates(rights, dateTypes).items():
            ESDoc._insertDate(newRights, date, dateType)
        
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

            for dateType, date in ESDoc._loadDates(agent, ['birth_date', 'death_date']).items():
                ESDoc._insertDate(esAgent, date, dateType)

            esAgent.roles = [agentRel.role]

            return esAgent
    
    @staticmethod
    def addInstance(instance):
        instanceData = {
            field: getattr(instance, field, None)
            for field in Instance.getFields()
        }
        esInstance = Instance(**instanceData)

        for dateType, date in ESDoc._loadDates(instance, ['pub_date']).items():
            ESDoc._insertDate(esInstance, date, dateType)
        
        if esInstance.pub_date:
            if esInstance.pub_date.gte:
                esInstance.pub_date_sort = esInstance.pub_date.gte
            if esInstance.pub_date.lte:
                esInstance.pub_date_sort_desc = esInstance.pub_date.lte

        #esInstance.identifiers = [
        #    ESDoc.addIdentifier(identifier)
        #    for identifier in instance.identifiers
        #]

        esInstance.agents = [
            ESDoc.addAgent(esInstance, agentInst)
            for agentInst in instance.agent_instances
        ]

        # NOTE: The two relationships are commented out as they are not
        # currently used in the front-end application. But this data may
        # prove to be useful in the future

        #esInstance.links = [
        #    ESDoc.addLink(link)
        #    for link in instance.links
        #]

        #esInstance.measurements = [
        #    ESDoc.addMeasurement(measure)
        #    for measure in instance.measurements
        #]

        esInstance.items = [
            ESDoc.addItem(item) 
            for item in instance.items if len(item.links) > 0
        ]

        esInstance.rights = [
            ESDoc.addRights(rights)
            for rights in instance.rights
        ]

        esInstance.language = [
            ESDoc.addLanguage(lang)
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
            ESDoc.addIdentifier(identifier)
            for identifier in item.identifiers
        ]
        
        #esItem.agents = [
        #    ESDoc.addAgent(esItem, agentItem)
        #    for agentItem in item.agent_items
        #]
        
        esItem.links = [
            ESDoc.addLink(link)
            for link in item.links
        ]

        for link in esItem.links:
            link.setLabel(esItem.source, esItem.identifiers[0].identifier)
        
        # NOTE: Similar to Instances above, these sections are not in use and
        # are being temporarily removed

        #esItem.measurements = [
        #    ESDoc.addMeasurement(measurement)
        #    for measurement in item.measurements
        #]
        
        #esItem.reports = [
        #    ESDoc.addReport(report)
        #    for report in item.access_reports
        #]

        #esItem.rights = [
        #    ESDoc.addRights(rights)
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
            ESDoc.addMeasurement(measure)
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
