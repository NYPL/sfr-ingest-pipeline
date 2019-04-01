import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model.core import Base
from model.work import Work
from model.instance import Instance
from model.item import Item

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
    return Session(autoflush=True)


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
        if 'data' in workData:
            record = workData
            workData = workData['data']

        primaryID = workData.pop('primary_identifier', None)

        existingWork = Work.lookupWork(
            session,
            workData.get('identifiers', []),
            primaryID
        )

        dbWork = Work.update(session, existingWork, workData)

        dbWork.date_modified = datetime.utcnow()
        return 'Work {}'.format(dbWork.uuid.hex)

    elif record['type'] == 'instance':
        logger.info('Ingesting instance record')
        instanceData = record['data']

        existingID = Instance.lookupInstance(
            session,
            instanceData.get('identifiers', []),
            instanceData.get('volume', None)    
        )
        print(existingID)
        existing = session.query(Instance).get(existingID)

        dbInstance = Instance.update(session, existing, instanceData)

        return 'Instance #{}'.format(dbInstance.id)

    elif record['type'] == 'item':
        logger.info('Ingesting item record')
        itemData = record['data']
        instanceID = itemData.pop('instance_id', None)

        existingID = Identifier.getByIdentifier(
            Item,
            session,
            itemData.get('identifiers', [])
        )
        existing = session.query(Item).get(existingID)

        dbItem = Item.update(session, existing, itemData)

        dbItem.instance.work.date_modified = datetime.utcnow()

        return 'Item #{}'.format(dbItem.id)
