import os
from polyglot.detect import Detector
from polyglot.detect.base import UnknownLanguage
from requests_aws4auth import AWS4Auth

from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch.exceptions import (
    ConnectionError,
    TransportError,
    ConflictError
)
from elasticsearch_dsl import connections
from elasticsearch_dsl.wrappers import Range

from sfrCore import SessionManager

from sqlalchemy.orm import configure_mappers

from model.elasticModel import (
    Work,
    Instance,
    Subject,
    Identifier,
    Agent,
    Language,
    Rights,
    MultiLanguage
)
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
        port = int(os.environ['ES_PORT'])
        timeout = int(os.environ['ES_TIMEOUT'])
        logger.info('Creating connection to ElasticSearch')
        awsauth = AWS4Auth(
            SessionManager.decryptEnvVar(os.environ['AWS_ACCESS']),
            SessionManager.decryptEnvVar(os.environ['AWS_SECRET']),
            'us-east-1',
            'es'
        )
        try:
            self.client = Elasticsearch(
                hosts=[{'host': host, 'port': port}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
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


class ElasticManager():
    def __init__(self, dbWork):
        self.dbWork = dbWork
        self.work = self.getCreateWork()
    
    def getCreateWork(self):
        logger.info('Indexing work {}'.format(self.dbWork))

        self.setSortTitle()

        workData = {
            field: getattr(self.dbWork, field, None)
            for field in Work.getFields()
        }

        for langField in Work.getLangFields():
            workData[langField] = self.setMultiLangField(getattr(self.dbWork, langField, None))

        esWork = Work.get(self.dbWork.uuid, ignore=404)
        if esWork is None:
            logger.debug('Creating new es doc for {}'.format(self.dbWork))
            return Work(meta={'id': self.dbWork.uuid}, **workData)
        else:
            logger.debug('Updating existing es doc {}'.format(esWork))
            self.updateWork(esWork, workData)
            return esWork

    
    def saveWork(self):
        logger.info('Saving es doc {}'.format(self.work))
        self.work.save()
    
    def updateWork(self, work, data):
        for key, value in data.items():
            logger.debug('Updating work field {} with {}'.format(key, value))
            setattr(work, key, value)

    def enhanceWork(self):
        """Build an ElasticSearch object from the provided postgresql ORM
        object. This builds a single object from the related tables of the 
        db object that can be indexed and searched in ElasticSearch.
        """
        logger.info('Adding additional metadata to {}'.format(self.work))
        self.work.issued_date = ElasticManager._loadDates(self.dbWork, ['issued'])[0]
        self.work.created_date = ElasticManager._loadDates(self.dbWork, ['created'])[0]

        self.work.alt_titles = [
            MultiLanguage(default=altTitle.title)
            for altTitle in self.dbWork.alt_titles
        ]

        self.work.subjects = [
            Subject(
                authority=subject.authority,
                uri=subject.uri,
                subject=self.setMultiLangField(subject.subject)
            )
            for subject in self.dbWork.subjects
        ]

        self.work.agents = []
        for agentWork in list(self.dbWork.agent_works):
            agent = ElasticManager.addAgent(self.work, agentWork)
            if agent is not None:
                logger.debug('Adding agent {}'.format(agentWork.agent.name))
                self.work.agents.append(agent)

        self.work.identifiers = {
            ElasticManager.addIdentifier(identifier)
            for identifier in self.dbWork.identifiers
        }

        self.work.languages = {
            ElasticManager.addLanguage(lang)
            for lang in self.dbWork.language
        }

        self.work.instances = []
        self.addInstances()

    @staticmethod
    def addIdentifier(identifier):
        idType = identifier.type
        if idType is None:
            idType = 'generic' 
        idRec = getattr(identifier, idType)[0]
        value = getattr(idRec, 'value')
        logger.debug('Adding identifier {} ({})'.format(value, idType))
        return Identifier(
            id_type=idType,
            identifier=value
        )

    @staticmethod
    def addLanguage(language):
        languageData = {
            field: getattr(language, field, None)
            for field in Language.getFields()
        }
        logger.debug('Adding language {}'.format(language.iso_3))
        return Language(**languageData)

    @staticmethod
    def addRights(rights):
        rightsData = {
            field: getattr(rights, field, None) for field in Rights.getFields()
        }
        newRights = Rights(**rightsData)

        logger.debug('Adding rights {}'.format(rightsData['license']))
        
        return newRights
    
    @staticmethod
    def addAgent(record, agentRel):
        match = list(filter(
            lambda x: True if agentRel.agent.name == x.name else False,
            record.agents
        ))
        if len(match) > 0:
            existing = match[0]
            existing.roles.append(agentRel.role)
            existing.roles = list(set(existing.roles))
            logger.debug('Adding role {} to existing agent {}'.format(
                agentRel.role, existing
            ))
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

            esAgent.roles = [agentRel.role]
            logger.debug('Adding new agent {}'.format(agent))
            return esAgent
    
    def addInstances(self):
        for instance in self.dbWork.instances:
            self.work.instances.append(self.addInstance(instance))

    def addInstance(self, instance):
        logger.info('Adding data from instance {}'.format(instance))
        instData = {
            field: getattr(instance, field, None)
            for field in Instance.getFields()
        }

        for langField in Instance.getLangFields():
            instData[langField] = self.setMultiLangField(getattr(instance, langField, None))

        instData['instance_id'] = instData.pop('id')
        newInst = Instance(**instData)

        newInst.pub_date = ElasticManager._loadDates(instance, ['pub_date', 'publication_date'])[0]
        if newInst.pub_date:
            if newInst.pub_date.gte:
                newInst.pub_date_sort = newInst.pub_date.gte
            if newInst.pub_date.lte:
                newInst.pub_date_sort_desc = newInst.pub_date.lte
        
        newInst.alt_titles = [
            MultiLanguage(default=altTitle.title)
            for altTitle in instance.alt_titles
        ]

        newInst.identifiers = {
            ElasticManager.addIdentifier(identifier)
            for identifier in instance.identifiers
        }

        newInst.agents = list(filter(None, [
            ElasticManager.addAgent(self.work, agentWork)
            for agentWork in list(instance.agent_instances)
        ]))

        newInst.rights = [
            ElasticManager.addRights(rights)
            for rights in instance.rights
        ]

        newInst.languages = [
            ElasticManager.addLanguage(lang)
            for lang in instance.language
        ]

        self.addItemsData(instance, newInst)

        newInst.cleanRels()

        return newInst
    
    def addItemsData(self, instance, esInst):
        esInst.formats = set()
        for item in instance.items:
            self.addItem(esInst, item)

    def addItem(self, instance, item):
        logger.info('Adding data from item {}'.format(item))
        instance.identifiers.update([
            ElasticManager.addIdentifier(identifier)
            for identifier in item.identifiers
        ])

        instance.formats.update([
            link.media_type for link in item.links
        ])
    
    @staticmethod
    def _loadDates(record, fields):
        retDates = []
        for date in record.dates:
            if date.date_type in fields:
                logger.debug('Adding date {} of type {}'.format(
                    date.display_date,
                    date.date_type
                ))
                retDates.append(
                    ElasticManager._formatDateRange(date)
                )
        return retDates if len(retDates) > 0 else [None]

    @staticmethod
    def _formatDateRange(date):
        if date.date_range is None:
                return
        dateRange = Range(
            gte=date.date_range.lower,
            lte=date.date_range.upper
        )
        logger.debug('Setting date range {}-{}'.format(
            date.date_range.lower,
            date.date_range.upper
        ))
        return dateRange

    def setSortTitle(self):
        if self.dbWork.sort_title is None:
            self.dbWork.setSortTitle()
    
    def setMultiLangField(self, text):
        if text is None:
            return None
        mlDoc = MultiLanguage(default=text)
        try:
            pgText = Detector(text)
            setattr(mlDoc, pgText.language.code, text)
        except UnknownLanguage:
            pass
        except AttributeError:
            logger.warning('Cannot analyze this language {}'.format(pgText.language.code))
            pass
        except Exception as err:
            logger.error('Caught unexpected error in language detection')
            logger.debug(err)
            
        return mlDoc
