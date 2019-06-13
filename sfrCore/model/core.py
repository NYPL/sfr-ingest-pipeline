
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from ..helpers import createLog

Base = declarative_base()

logger = createLog('core_model')

class Core(object):
    """A mixin for other SQLAlchemy ORM classes. Includes a date_craeted and
    date_updated field for all database tables."""
    date_created = Column(
        DateTime,
        default=datetime.utcnow()
    )

    date_modified = Column(
        DateTime,
        default=datetime.utcnow(),
        onupdate=datetime.utcnow()
    )
