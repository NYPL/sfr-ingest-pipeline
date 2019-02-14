import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

from model.core import Base
from model.work import Work

from helpers.logHelpers import createLog
from helpers.errorHelpers import DBError

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


def retrieveRecord(session, recordType, recordID):
    """Retrieve the given record from the postgreSQL instance"""
    if recordType == 'work':
        logger.info('Retrieving record identifier by {}'.format(recordID))
        workRec = session.query(Work)\
            .options(joinedload(Work.identifiers))\
            .options(joinedload(Work.agents))\
            .options(joinedload(Work.subjects))\
            .options(joinedload(Work.dates))\
            .options(joinedload(Work.instances))\
            .options(joinedload(Work.instances).joinedload(Instance.identifiers))\
            .options(joinedload(Work.instances).joinedload(Instance.agents))\
            .options(joinedload(Work.instances).joinedload(Instance.measurements))\
            .options(joinedload(Work.instances).joinedload(Instance.links))\
            .options(joinedload(Work.instances).joinedload(Instance.items).joinedload(Item.links))\
            .options(joinedload(Work.instances).joinedload(Instance.items).joinedload(Item.agents))\
            .options(joinedload(Work.instances).joinedload(Instance.items).joinedload(Item.identifiers))\
            .options(joinedload(Work.instances).joinedload(Instance.items).joinedload(Item.measurements))\
            .filter(Work.uuid == recordID).one()
        return workRec
    else:
        logger.warning('Indexing of non-work records not currently supported')
        raise DBError('work', 'Does not support indexing non-work tables')

def retrieveAllRecords(session):
    return session.query(Work).all()
