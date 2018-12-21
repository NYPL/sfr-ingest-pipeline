import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from model.core import Base
from model.work import Work

username = os.environ['DB_USER']
password = os.environ['DB_PASS']
host = os.environ['DB_HOST']
port = os.environ['DB_PORT']
database = os.environ['DB_NAME']

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
        op, work = Work.updateOrInsert(session, workData)

        if op == 'insert':
            print("Inserting work!", work)
            print(work.agents)
            print(work.identifiers)
            print(work.instances)
            print(work.subjects)
            print(work.__dict__)
            session.add(work)
