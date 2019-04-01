
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from helpers.logHelpers import createLog

Base = declarative_base()

logger = createLog('core_model')

class Core(object):
    """A mixin for other SQLAlchemy ORM classes. Includes a date_craeted and
    date_updated field for all database tables."""
    date_created = Column(
        DateTime,
        default=datetime.now()
    )

    date_modified = Column(
        DateTime,
        default=datetime.now(),
        onupdate=datetime.now()
    )

    def updateFields(self, **kwargs):
        for key, value in kwargs.items():
            if key in dir(self):
                setattr(self, key, value)
            else:
                logger.warning('Field {} is not valid for model {}'.format(
                    key,
                    self
                ))
