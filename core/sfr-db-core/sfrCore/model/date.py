import re
from dateutil.parser import parse
from datetime import date
import calendar
from calendar import monthrange, IllegalMonthError
from sqlalchemy import (
    Table,
    Column,
    Unicode,
    Integer,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import DATERANGE
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import MultipleResultsFound

from .core import Base, Core

from ..helpers import createLog

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
        try:
            outDate = DateField.lookupDate(session, dateInst, model, recordID)
        except MultipleResultsFound:
            outDate = DateField.mergeDates(session, dateInst, model, recordID)
        if outDate:
            logger.info('Updating existing date record {}'.format(outDate.id))
            outDate.update(dateInst)
        else:
            logger.info('Inserting new date object')
            outDate = DateField.insert(dateInst)

        return outDate

    @classmethod
    def mergeDates(cls, session, dateInst, model, recordID):
        dupeDates = session.query(cls)\
            .join(model.__tablename__)\
            .filter(model.id == recordID)\
            .filter(cls.date_type == dateInst['date_type'])\
            .all()

        dupeDates.sort(key=lambda d: d.date_modified)

        for i in range(1, len(dupeDates)):
            if dupeDates[i].date_range:
                dupeDates[0].display_date = dupeDates[i].display_date
                dupeDates[0].date_range = dupeDates[i].date_range
            session.delete(dupeDates[i])

        return dupeDates[0]

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
        DateField.cleanDateData(dateData)
        self.setDateRange(dateData['date_range'])
        self.display_date = dateData['display_date']

    @classmethod
    def insert(cls, dateData):
        """Insert a new date row"""
        newDate = DateField()
        DateField.cleanDateData(dateData)
        for field, value in dateData.items():
            if field != 'date_range': setattr(newDate, field, value)
            else: newDate.setDateRange(dateData['date_range'])
        return newDate

    @classmethod
    def cleanDateData(cls, dateData):
        dateData['date_range'] = dateData['date_range'].strip(' ©.')
        dateData['display_date'] = dateData['display_date'].strip(' .[]')
        bracketMatch = re.search(r'\[([\d\-\?u%~©]+)\]', dateData['date_range'])
        if bracketMatch: 
            dateData['date_range'] = bracketMatch.group(1)
        if re.search(r'(?:(?<=[0-9])[\?u%~X]+|\-(?![0-9]+)|^(?:c|ca.|c.|ca)(?=[0-9]))', dateData['date_range']):
            try:
                DateField.parseUncertainty(dateData)
            except KeyError:
                logger.error('Unable to parse uncertain date {}'.format(dateData['date_range']))

    @classmethod
    def parseUncertainty(cls, dateData):
        rawDates = re.findall(r'((?:(?:c|ca.|c.|ca))(?=[0-9])|)(\d+)((?:[\?u%~X]*||(?:\-(?![0-9]+))))', dateData['date_range'])
        if len(rawDates) == 1:
            parsedDate = DateField.setUncertainDates(rawDates[0])
            dateData['date_range'] =  '{}/{}'.format(
                parsedDate['range']['start'],
                parsedDate['range']['end']
            )
            dateData['display_date'] = parsedDate['display']
        elif len(rawDates) == 2:
            startParsedDate = DateField.setUncertainDates(rawDates[0])
            endParsedDate = DateField.setUncertainDates(rawDates[1])
            dateData['date_range'] = '{}/{}'.format(
                startParsedDate['range']['start'],
                endParsedDate['range']['end']
            )
            dateData['display_date'] = '{}/{}'.format(
                startParsedDate['display'],
                endParsedDate['display']
            )

    @classmethod
    def setUncertainDates(cls, matchObj):
        innerDate = {}
        circaChar = matchObj[0]
        dateStr = matchObj[1]
        fuzzyChar = matchObj[2]
        if len(dateStr) == 1:
            innerDate['range'] =  {
                'start': '{}000'.format(dateStr),
                'end': '{}999'.format(dateStr)
            }
            innerDate['display'] = '{}XXX'.format(dateStr)
        if len(dateStr) == 2:
            innerDate['range'] =  {
                'start': '{}00'.format(dateStr),
                'end': '{}99'.format(dateStr)
            }
            innerDate['display'] = '{}XX'.format(dateStr)
        elif len(dateStr) == 3:
            innerDate['range'] =  {
                'start': '{}0'.format(dateStr),
                'end': '{}9'.format(dateStr)
            }
            innerDate['display'] = '{}X'.format(dateStr)
        elif len(dateStr) == 4:
            dateInt = int(dateStr)
            if fuzzyChar != '' or circaChar != '':
                innerDate['range'] =  {
                    'start': str(dateInt - 1),
                    'end': str(dateInt + 1)
                }
                innerDate['display'] = '{}?'.format(dateStr)
            else:
                innerDate['range'] = {
                    'start': dateStr,
                    'end': dateStr
                }
                innerDate['display'] = dateStr
        return innerDate

    def setDateRange(self, dateObj):
        logger.info('Parsing date string {} into date range'.format(dateObj))
        try:
            if type(dateObj) is list:
                logger.debug('Received start/end dates, treat as bounds')
                startYear = parse(dateObj[0]).year
                endYear = parse(dateObj[1]).year
                self.date_range = '[{}, {})'.format(
                    date(startYear, 1, 1),
                    date(endYear, 12, 31)
                )
            elif re.match(r'^[0-9]{4}$', dateObj):
                logger.debug('Received year value, parsing into full year')
                year = parse(dateObj).year
                self.date_range =  '[{}, {})'.format(
                    date(year, 1, 1),
                    date(year, 12, 31)
                )
            elif re.match(r'^[0-9]{4}(?:/|-)[0-9]{4}$', dateObj):
                if '-' in dateObj:
                    dateYears = dateObj.split('-')
                    self.display_date = self.display_date.replace('-', '/')
                else:
                    dateYears = dateObj.split('/')
                startYear = parse(dateYears[0]).year
                endYear = parse(dateYears[1]).year
                if endYear < startYear:
                    raise ValueError
                self.date_range = '[{}, {})'.format(
                    date(startYear, 1, 1),
                    date(endYear, 12, 31)
                )
            elif re.match(r'^[0-9]{4}-[0-9]{2}$', dateObj):
                logger.debug('Received year-month, parsing into month range')
                try:
                    dateObj = parse(dateObj)
                    year = dateObj.year
                    month = dateObj.month
                    lastDay = monthrange(year, month)[1]  # Accounts for leap years
                    self.date_range = '[{}, {})'.format(
                        date(year, month, 1),
                        date(year, month, lastDay)
                    )
                except (IllegalMonthError, TypeError):
                    logger.debug('Year-month is actually year-2 dig year')
                    secondYear = '{}{}'.format(dateObj[:2], dateObj[5:])
                    self.display_date = '{}/{}'.format(dateObj[:4], secondYear)
                    self.setDateRange(self.display_date)
            else:
                logger.debug('Received other value, treating as single date')
                self.date_range = '[{},)'.format(
                    str(parse(dateObj).date())
                )
        except ValueError as err:
            logger.error('Could not parse date string {}'.format(dateObj))
            logger.debug('Returning None for date_range, date unsearchable')
            self.date_range = None
