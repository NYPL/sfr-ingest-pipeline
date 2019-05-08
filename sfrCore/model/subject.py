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
from sqlalchemy.orm.exc import MultipleResultsFound

from sfrCore.model.core import Base, Core
from sfrCore.model.measurement import SUBJECT_MEASUREMENTS, Measurement

from sfrCore.helpers.logger import createLog
from sfrCore.helpers.errors import DBError

logger = createLog('subjects')

SUBJECT_WORKS = Table(
    'subject_works', Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id'), index=True),
    Column('subject_id', Integer, ForeignKey('subjects.id'), index=True),
    Column('weight', Float)
)


class Subject(Core, Base):
    """A generic model for storing subject heading data from any authority"""
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    authority = Column(Unicode, index=True)
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
        back_populates='subject',
        collection_class=set
    )

    def __repr__(self):
        return '<Subject(subject={}, uri={}, authority={})'.format(
            self.subject,
            self.uri,
            self.authority
        )

    @classmethod
    def updateOrInsert(cls, session, subject):
        """Query for an existing subject, and if found, update existing record,
        otherwise insert a new subject"""
        measurements = subject.pop('measurements', [])

        outSubj = Subject.lookupSubject(session, subject)

        if outSubj is None: outSubj = Subject.insert(subject, measurements)
        else: outSubj.update(session, subject, measurements)
        
        return outSubj

    def update(self, session, subject, measurements):
        """Update existing subject record"""
        
        for field, value in subject.items():
            if value is not None:
                if type(value) is str and value.strip() != '':
                    setattr(self, field, value)
                else:
                    setattr(self, field, value)

        # TODO: Move measurements to relationship between subject and record
        # It does not make sense for this data to be stored here. (Unless we
        # update what data a measurement encodes.)
        self.updateMeasurements(session, measurements)

    @classmethod
    def insert(cls, subject, measurements):
        """Insert a new subject"""
        newSubject = Subject(**subject)

        # TODO Remove measurement as per above
        newSubject.addMeasurements(measurements)
        
        return newSubject
    
    def addMeasurements(self):
        newSubject.measurements = {
            Measurement.insert(m) for m in measurements
        }

    def updateMeasurements(self, session, measurements):
        for measure in measurements:
            self.measurements.add(
                Measurement.updateOrInsert(session, measure, Subject, self.id)
            )

    @classmethod
    def lookupSubject(cls, session, subject):
        """Query database for an existing subject. If multiple are found,
        raise an error, otherwise return the subject record."""
        try:
            return session.query(Subject)\
                .filter(Subject.authority == subject['authority'])\
                .filter(Subject.subject == subject['subject'])\
                .one_or_none()
        except MultipleResultsFound:
            logger.error('Too many subjects found for {}'.format(
                subject['subject']
            ))
            raise DBError('subjects', 'Found multiple subject entries')
