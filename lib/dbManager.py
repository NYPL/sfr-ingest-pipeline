import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from model.core import Base
from model.work import Work
from model.item import Item

from lib.queryManager import queryWork
from lib.outputManager import OutputManager

username = os.environ['DB_USER']
password = os.environ['DB_PASS']
host = os.environ['DB_HOST']
port = os.environ['DB_PORT']
database = os.environ['DB_NAME']


LOOKUP_IDENTIFIERS = [
    'oclc', # OCLC Number
    'isbn', # ISBN (10 or 13)
    'issn', # ISSN
    'upc',  # UPC (Probably unused)
    'lccn', # LCCN
    'swid', # OCLC Work Identifier
    'stdnbr'# Sandard Number (unclear)
]

def dbGenerateConnection():

    engine = create_engine(
        'postgresql://{}:{}@{}:{}/{}'.format(
            username,
            password,
            host,
            port,
            database
        )
    )

    if not engine.dialect.has_table(engine, 'works'):
        Base.metadata.create_all(engine)

    return engine


def createSession(engine):
    Session = sessionmaker(bind=engine)
    return Session()

def importRecord(session, record):

    if 'type' not in record:
        record['type'] = 'work'

    if record['type'] == 'work':
        workData = (record['data'])
        op, dbWork = Work.updateOrInsert(session, workData)

        if op == 'insert':
            session.add(dbWork)
            session.flush()

        if record['method'] == 'insert':
            queryWork(dbWork, dbWork.uuid.hex)

        # Put Resulting identifier in SQS to be ingested into Elasticsearch
        OutputManager.putQueue({
            'type': record['type'],
            'identifier': dbWork.uuid.hex
        })

        return op, dbWork.uuid.hex
    elif record['type'] == 'item':
        itemData = record['data']

        op, dbItem = Item.updateOrInsert(session, itemData)
