import re
from dateutil.parser import parse
from datetime import date
from calendar import monthrange
from psycopg2.extras import DateRange
from sqlalchemy import (
    Table,
    Column,
    Unicode,
    Integer,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import DATERANGE
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import text
from sqlalchemy.orm.exc import NoResultFound

from .core import Base, Core

from ..helpers import createLog, DBError

logger = createLog('dateModel')

WORK_DATES = Table(
    'work_dates',
    Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id'), index=True),
    Column('date_id', Integer, ForeignKey('dates.id'), index=True)
)

INSTANCE_DATES = Table(
    'instance_dates',
    Base.metadata,
    Column('instance_id', Integer, ForeignKey('instances.id'), index=True),
    Column('date_id', Integer, ForeignKey('dates.id'), index=True)
)

ITEM_DATES = Table(
    'item_dates',
    Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id'), index=True),
    Column('date_id', Integer, ForeignKey('dates.id'), index=True)
)

AGENT_DATES = Table(
    'agent_dates',
    Base.metadata,
    Column('agent_id', Integer, ForeignKey('agents.id'), index=True),
    Column('date_id', Integer, ForeignKey('dates.id'), index=True)
)

RIGHTS_DATES = Table(
    'rights_dates',
    Base.metadata,
    Column('rights_id', Integer, ForeignKey('rights.id'), index=True),
    Column('date_id', Integer, ForeignKey('dates.id'), index=True)
)

class DateField(Core, Base):
    """An abstract class that represents a date value, associated with any
    entity or record in the SFR data model. This class contains a set of fields
    that store both human-readable and parsable date range values. While an
    ISO-8601 value is recommended for the human-readable component this
    is not required
    @value display_date
    @value date_range
    @value date_type"""

    __tablename__ = 'dates'
    id = Column(Integer, primary_key=True)
    display_date = Column(Unicode)
    date_range = Column(DATERANGE)
    date_type = Column(Unicode, index=True)

    works = relationship(
        'Work',
        secondary=WORK_DATES,
        backref=backref('dates', collection_class=set)
    )
    instances = relationship(
        'Instance',
        secondary=INSTANCE_DATES,
        backref=backref('dates', collection_class=set)
        
    )
    items = relationship(
        'Item',
        secondary=ITEM_DATES,
        backref=backref('dates', collection_class=set)
    )
    agents = relationship(
        'Agent',
        secondary=AGENT_DATES,
        backref=backref('dates', collection_class=set)
    )
    rights = relationship(
        'Rights',
        secondary=RIGHTS_DATES,
        backref=backref('dates', collection_class=set)
    )

    def __repr__(self):
        return '<Date(date={})>'.format(self.display_date)

    @classmethod
    def updateOrInsert(cls, session, dateInst, model, recordID):
        logger.debug('Inserting or updating date {}'.format(
            dateInst['display_date'])
        )
        """Query the database for a date on the current record. If found,
        update the existing date, if not, insert new row"""
        outDate = DateField.lookupDate(session, dateInst, model, recordID)
        if outDate:
            logger.info('Updating existing date record {}'.format(outDate.id))
            outDate.update(dateInst)
        else:
            logger.info('Inserting new date object')
            outDate = DateField.insert(dateInst)
        
        return outDate

    @classmethod
    def lookupDate(cls, session, dateInst, model, recordID):
        """Query database for link related to current record. Return link
        if found, otherwise return None"""
        return session.query(cls)\
            .join(model.__tablename__)\
            .filter(model.id == recordID)\
            .filter(cls.date_type == dateInst['date_type'])\
            .one_or_none()
    
    def update(self, dateData):
        """Update fields on existing date"""
        newRange = DateField.parseDate(dateData['date_range'])
        if newRange != self.date_range:
            self.date_range = newRange
            self.display_date = dateData['display_date']

    @classmethod
    def insert(cls, dateData):
        """Insert a new date row"""
        newDate = DateField()
        for field, value in dateData.items():
            if field != 'date_range': setattr(newDate, field, value)
            else: newDate.setDateRange(dateData['date_range'])
        return newDate

    def setDateRange(self, dateObj):
        logger.info('Parsing date string {} into date range'.format(dateObj))
        try:
            if type(dateObj) is list:
                logger.debug('Received start/end dates, treat as bounds')
                self.date_range = '[{}, {})'.format(
                    parse(dateObj[0]).date(),
                    parse(dateObj[1]).date()
                )
            elif re.match(r'^[0-9]{4}$', dateObj):
                logger.debug('Received year value, parsing into full year')
                year = parse(dateObj).year
                self.date_range =  '[{}, {})'.format(
                    date(year, 1, 1),
                    date(year, 12, 31)
                )
            elif re.match(r'^[0-9]{4}-[0-9]{2}$', dateObj):
                logger.debug('Received year-month, parsing into month range')
                dateObj = parse(dateObj)
                year = dateObj.year
                month = dateObj.month
                lastDay = monthrange(year, month)[1]  # Accounts for leap years
                self.date_range = '[{}, {})'.format(
                    date(year, month, 1),
                    date(year, month, lastDay)
                )
            else:
                logger.debug('Received other value, treating as single date')
                self.date_range = '[{},)'.format(
                    str(parse(dateObj).date())
                )
        except ValueError as err:
            logger.error('Could not parse date string {}'.format(dateObj))
            logger.debug('Returning None for date_range, date unsearchable')
            self.date_range = None
