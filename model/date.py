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
from sqlalchemy.orm import relationship
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


class Date(Core, Base):
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

    work = relationship(
        'Work',
        secondary=WORK_DATES,
        back_populates='dates'
    )
    instance = relationship(
        'Instance',
        secondary=INSTANCE_DATES,
        back_populates='dates'
    )
    item = relationship(
        'Item',
        secondary=ITEM_DATES,
        back_populates='dates'
    )
    agent = relationship(
        'Agent',
        secondary=AGENT_DATES,
        back_populates='dates'
    )

    def __repr__(self):
        return '<Date(date={})>'.format(self.display_date)

    @classmethod
    def updateOrInsert(cls, session, date, model, recordID):
        """Query the database for a date on the current record. If found,
        update the existing date, if not, insert new row"""
        existing = Date.lookupDate(session, date, model, recordID)
        if existing is not None:
            Date.update(existing, link)
            return None

        return Date.insert(date)

    @classmethod
    def update(cls, existing, date):
        """Update fields on existing date"""
        for field, value in date.items():
            if(
                value is not None
                and value.strip() != ''
                and field != 'date_range'
            ):
                setattr(existing, field, value)

        existing.date_range = Date.parseDate(date['date_range'])

    @classmethod
    def insert(cls, dateData):
        """Insert a new date row"""
        date = Date()
        for field, value in dateData.items():
            if field != 'date_range':
                setattr(date, field, value)
            else:
                setattr(date, field, Date.parseDate(value))

        return date

    @classmethod
    def lookupDate(cls, session, link, model, recordID):
        """Query database for link related to current record. Return link
        if found, otherwise return None"""
        return session.query(cls)\
            .join(model.__tablename__)\
            .filter(model.id == recordID)\
            .filter(cls.date_type == date['date_type'])\
            .one_or_none()

    @staticmethod
    def parseDate(date):
        if type(date) is list:
            return DateRange(parse(date[0]), parse(date[1]))
        elif re.match(r'^[0-9]{4}$', date):
            year = parse(date).year
            return DateRange(date(year, 1, 1), date(year, 12, 31))
        elif re.match(r'^[0-9]{4}-[0-9]{2}$', date):
            dateObj = parse(date)
            year = dateObj.year
            month = dateObj.month
            lastDay = monthrange(year, month)[1]  # Accounts for leap years
            return DateRange(date(year, month, 1), date(year, month, lastDay))
        else:
            return DateRange(parse(date), None)
