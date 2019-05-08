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

from model.core import Base, Core

from helpers.errorHelpers import DBError
from helpers.logHelpers import createLog

logger = createLog('dateModel')

WORK_DATES = Table(
    'work_dates',
    Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id')),
    Column('date_id', Integer, ForeignKey('dates.id'))
)

INSTANCE_DATES = Table(
    'instance_dates',
    Base.metadata,
    Column('instance_id', Integer, ForeignKey('instances.id')),
    Column('date_id', Integer, ForeignKey('dates.id'))
)

ITEM_DATES = Table(
    'item_dates',
    Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id')),
    Column('date_id', Integer, ForeignKey('dates.id'))
)

AGENT_DATES = Table(
    'agent_dates',
    Base.metadata,
    Column('agent_id', Integer, ForeignKey('agents.id')),
    Column('date_id', Integer, ForeignKey('dates.id'))
)

RIGHTS_DATES = Table(
    'rights_dates',
    Base.metadata,
    Column('rights_id', Integer, ForeignKey('rights.id')),
    Column('date_id', Integer, ForeignKey('dates.id'))
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
    display_date = Column(Unicode, index=True)
    date_range = Column(DATERANGE, index=True)
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
        logger.debug('Inserting or updating date {}'.format(dateInst['display_date']))
        """Query the database for a date on the current record. If found,
        update the existing date, if not, insert new row"""
        outDate = DateField.lookupDate(session, dateInst, model, recordID)
        if outDate is None:
            logger.info('Inserting new date object')
            outDate = DateField.insert(dateInst)
        else:
            logger.info('Updating existing date record {}'.format(outDate.id))
            DateField.update(outDate, dateInst)
        
        return outDate

    @classmethod
    def update(cls, existing, dateInst):
        """Update fields on existing date"""
        newRange = DateField.parseDate(dateInst['date_range'])
        if newRange != existing.date_range:
            existing.date_range = newRange
            existing.display_date = dateInst['display_date']

    @classmethod
    def insert(cls, dateData):
        """Insert a new date row"""
        dateInst = cls()
        for field, value in dateData.items():
            if field != 'date_range':
                setattr(dateInst, field, value)
            else:
                setattr(dateInst, field, DateField.parseDate(value))

        return dateInst

    @classmethod
    def lookupDate(cls, session, dateInst, model, recordID):
        """Query database for link related to current record. Return link
        if found, otherwise return None"""
        return session.query(cls)\
            .join(model.__tablename__)\
            .filter(model.id == recordID)\
            .filter(cls.date_type == dateInst['date_type'])\
            .one_or_none()

    @staticmethod
    def parseDate(dateObj):
        """This generates daterange strings compatible with postgres. It should
        be able to use the psycopg2.extra model, but that does not work for
        some reason. That should be fixed and used here."""

        logger.info('Parsing date string {} into date range'.format(dateObj))

        try:
            if type(dateObj) is list:
                logger.debug('Recieved list of dates, treating as start/end bounds')
                return '[{}, {})'.format(parse(dateObj[0]).date(), parse(dateObj[1]).date())
                #return DateRange(parse(date[0]), parse(date[1]))
            elif re.match(r'^[0-9]{4}$', dateObj):
                logger.debug('Recieved year value, parsing into full year range')
                year = parse(dateObj).year
                return '[{}, {})'.format(date(year, 1, 1), date(year, 12, 31))
                #return DateRange(date(year, 1, 1), date(year, 12, 31))
            elif re.match(r'^[0-9]{4}-[0-9]{2}$', dateObj):
                logger.debug('Recieved year-month, parsing into month range')
                dateObj = parse(dateObj)
                year = dateObj.year
                month = dateObj.month
                lastDay = monthrange(year, month)[1]  # Accounts for leap years
                return '[{}, {})'.format(date(year, month, 1), date(year, month, lastDay))
                #return DateRange(date(year, month, 1), date(year, month, lastDay))
            else:
                logger.debug('Received other value, treating as single date')
                return '[{},)'.format(str(parse(dateObj).date()))
                #DateRange(parse(date), None, bounds='[]')
        except ValueError as err:
            logger.error('Could not parse date string {}'.format(dateObj))
            logger.debug('Returing None for date_range, will still be displayed, but unsearchable')
            return None
