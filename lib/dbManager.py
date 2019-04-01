import os
from datetime import datetime
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
    Session = sessionmaker(bind=engine, autoflush=True)
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
        if 'data' in workData:
            record = workData
            workData = workData['data']
        
        primaryID = workData.pop('primary_identifier', None)
        workUUID = Work.lookupWork(session, workData['identifiers'], primaryID)
        if workUUID is not None:
            logger.info('Found exsting work {}. Placing record in update stream'.format(
                workUUID
            ))
            workData['primary_identifier'] = {
                'type': 'uuid',
                'identifier': workUUID.hex,
                'weight': 1
            }
            # TODO Create stream and make configurable in env file
            OutputManager.putKinesis(workData, 'sfr-db-update-development')
            return 'Existing work {}'.format(workUUID)

        dbWork = Work.insert(session, workData)

        queryWork(session, dbWork, dbWork.uuid.hex)

        return dbWork.uuid.hex

    elif record['type'] == 'instance':
        logger.info('Ingesting instance record')
        instanceData = record['data']

        instanceID = Identifier.getByIdentifier(Instance, session, instanceData['identifiers'])
        if instanceID is not None:
            logger.info('Found exsting instance {}. Placing in update stream'.format(
                instanceID
            ))
            instanceData['primary_identifier'] = {
                'type': 'row_id',
                'identifier': instanceID,
                'weight': 1
            }
            OutputManager.putKinesis(instanceData, 'sfr-db-update-development')
            return 'Existing instance Row ID {}'.format(instanceID)

        dbInstance = Instance.insert(session, instanceData)

        dbInstance.work.date_modfied = datetime.utcnow()

        return 'Instance #{}'.format(dbInstance.id)

    elif record['type'] == 'item':
        logger.info('Ingesting item record')
        itemData = record['data']
        
        itemID = Identifier.getByIdentifier(Item, session, itemData['identifiers'])
        if itemID is not None:
            logger.info('Found exsting item {}. Placing in update stream'.format(
                itemID
            ))
            itemData['primary_identifier'] = {
                'type': 'row_id',
                'identifier': itemID,
                'weight': 1
            }
            OutputManager.putKinesis(itemData, 'sfr-db-update-development')
            return 'Existing item Row ID {}'.format(itemID)

        instanceID = itemData.pop('instance_id', None)

        dbItem = Item.insert(session, itemData)

        logger.debug('Got new item record, adding to instance')
        Instance.addItemRecord(session, instanceID, dbItem)
        
        dbItem.instance.work.date_modified = datetime.utcnow()

        return 'Item #{}'.format(dbItem.id)

    elif record['type'] == 'access_report':
        logger.info('Ingest Accessibility Report')
        reportData = record['data']

        dbItem = Item.addReportData(session, reportData)
        
        if dbItem is not None:
            dbItem.instance.work.date_modified = datetime.utcnow()
