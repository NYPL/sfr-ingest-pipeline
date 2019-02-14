from sqlalchemy import (
    Table,
    Column,
    Integer,
    ForeignKey,
    Unicode,
    Float,
    String
)
from sqlalchemy.orm import relationship

from model.core import Base, Core
from model.measurement import SUBJECT_MEASUREMENTS, Measurement

from helpers.logHelpers import createLog
from helpers.errorHelpers import DBError

logger = createLog('subjects')

SUBJECT_WORKS = Table(
    'subject_works', Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id')),
    Column('subject_id', Integer, ForeignKey('subjects.id')),
    Column('weight', Float)
)


class Subject(Core, Base):
    """A generic model for storing subject heading data from any authority"""
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    authority = Column(Unicode)
    uri = Column(String(50))
    subject = Column(Unicode, index=True)
    weight = Column(Float)

    work = relationship(
        'Work',
        secondary=SUBJECT_WORKS,
        back_populates='subjects'
    )
    measurements = relationship(
        'Measurement',
        secondary=SUBJECT_MEASUREMENTS,
        back_populates='subject'
    )

    def __repr__(self):
        return '<Subject(subject={}, uri={}, authority={})'.format(
            self.subject,
            self.uri,
            self.authority
        )
