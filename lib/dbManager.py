import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model.core import Base
from model.work import Work
from model.instance import Instance
from model.item import Item

from lib.queryManager import queryWork
from lib.outputManager import OutputManager

from helpers.logHelpers import createLog

logger = createLog('db_manager')

# Load environemnt variables for database connection
USERNAME = os.environ['DB_USER']
PASSWORD = os.environ['DB_PASS']
HOST = os.environ['DB_HOST']
PORT = os.environ['DB_PORT']
DATABASE = os.environ['DB_NAME']


def dbGenerateConnection():
    """Helper function that generates sqlAlchemy engine from database details
    provided in configuration files and loaded as environment variables"""
    engine = create_engine(
        'postgresql://{}:{}@{}:{}/{}'.format(
            USERNAME,
            PASSWORD,
            HOST,
            PORT,
            DATABASE
        )
    )

    # If the database does not exist yet, create database from the local model
    if not engine.dialect.has_table(engine, 'works'):
        Base.metadata.create_all(engine)

    return engine


def createSession(engine):
    """Create a single database session"""
    Session = sessionmaker(bind=engine)
    return Session()


def importRecord(session, record):
    """Import a generic record. Fields within the record, type and method
    control exactly what methods are invoked. Specifically this process will be
    implemented to insert and update:
    - works
    - instances
    - items
    - agents
    - subjects
    - access_reports"""
    if 'type' not in record:
        record['type'] = 'work'

    if record['type'] == 'work':
        workData = (record['data'])
        op, dbWork = Work.updateOrInsert(session, workData)

        if op == 'insert':
            session.add(dbWork)
            session.flush()

        # If this is a newly fetched record, retrieve additional data from the
        # enhancement process. Specifically pass identifying information to
        # a Kinesis stream that will processed by the OCLC Classify service
        # and others
        if record['method'] == 'insert':
            queryWork(dbWork, dbWork.uuid.hex)

        # Put Resulting identifier in SQS to be ingested into Elasticsearch
        OutputManager.putQueue({
            'type': record['type'],
            'identifier': dbWork.uuid.hex
        })

        return op, dbWork.uuid.hex

    elif record['type'] == 'instance':
        logger.info('Ingesting instance record')
        instanceData = record['data']

        dbInstance = Instance.updateOrInsert(session, instanceData)

        if dbInstance is not None:
            logger.warning('Could not find existing record for instance {}'.format(dbInstance.id))
        
        OutputManager.putQueue({
            'type': 'work',
            'identifier': dbInstance.work.uuid.hex
        })

    elif record['type'] == 'item':
        logger.info('Ingesting item record')
        itemData = record['data']
        instanceID = itemData.pop('instance_id', None)

        dbItem = Item.updateOrInsert(session, itemData)

        if dbItem is not None:
            logger.debug('Got new item record, adding to instance')
            # Add item to parent instance record
            Instance.addItemRecord(session, instanceID, dbItem)
            session.add(dbItem)
            session.flush()
        
        OutputManager.putQueue({
            'type': 'work',
            'identifier': dbItem.instance.work.uuid.hex
        })

    elif record['type'] == 'access_report':
        logger.info('Ingest Accessibility Report')
        reportData = record['data']

        Item.addReportData(session, reportData)
