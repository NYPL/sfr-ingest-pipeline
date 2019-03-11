import re
from dateutil.parser import parse
from datetime import date
from calendar import monthrange
from sqlalchemy import (
    Table,
    Column,
    Unicode,
    Integer,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import DATERANGE
from sqlalchemy.orm import relationship

from model.core import Base, Core

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
    @value date_type
    """

    __tablename__ = 'dates'
    id = Column(Integer, primary_key=True)
    display_date = Column(Unicode, index=True)
    date_range = Column(DATERANGE, index=True)
    date_type = Column(Unicode, index=True)

    works = relationship(
        'Work',
        secondary=WORK_DATES,
        backref='dates'
    )
    instances = relationship(
        'Instance',
        secondary=INSTANCE_DATES,
        backref='dates'
    )
    items = relationship(
        'Item',
        secondary=ITEM_DATES,
        backref='dates'
    )
    agents = relationship(
        'Agent',
        secondary=AGENT_DATES,
        backref='dates'
    )
    rights = relationship(
        'Rights',
        secondary=RIGHTS_DATES,
        backref='dates'
    )

    rights = relationship(
        'Rights',
        secondary=RIGHTS_DATES,
        backref='dates'
    )

    def __repr__(self):
        return '<DateField(date={})>'.format(self.display_date)

