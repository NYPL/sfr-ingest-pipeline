
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


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
            setattr(self, key, value)
    
    def loadDates(self, fields):
        retDates = {}
        for date in self.dates:
            if date.date_type in fields:
                retDates[date.date_type] = {
                    'range': date.date_range,
                    'display': date.display_date
                }
        return retDates
