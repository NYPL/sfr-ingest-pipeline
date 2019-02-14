import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

from model.core import Base
from model.work import Work
from model.instance import Instance
from model.item import Item

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


def retrieveRecords(session, es):
    """Retrieve all recently updated works in the SFR database and generate
    elasticsearch-dsl ORM objects.
    """
    logger.debug('Loading Records updated in last {} seconds'.format(
        os.environ['INDEX_PERIOD'])
    )
    
    fetchPeriod = datetime.now() - timedelta(seconds=int(os.environ['INDEX_PERIOD']))
    
    works = session.query(Work).filter(Work.date_modified >= fetchPeriod).all()
    
    logger.info('Retrieved {} works for indexing'.format(len(works)))

    for w in works:
        es.indexRecord(w)
