
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Core(object):

    date_created = Column(DateTime, default=datetime.now())
    date_modified = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
