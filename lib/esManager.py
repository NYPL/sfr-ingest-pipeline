import os
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError
from elasticsearch_dsl import connections

from model.elasticDocs import Work

from helpers.logHelpers import createLog
from helpers.errorHelpers import ESError

logger = createLog('es_manager')

class ESConnection():
    def __init__(self):
        self.index = os.environ['ES_INDEX']
        self.client = None

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
        return True
