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

        if outSubj is None:
            outSubj = Subject.insert(
                subject,
                measurements=measurements
            )
        
        else: 
            Subject.update(
                session,
                outSubj,
                subject,
                measurements=measurements
            )
        
        return outSubj


    @classmethod
    def update(cls, session, existing, subject, **kwargs):
        """Update existing subject record"""
        measurements = kwargs.get('measurements', [])

        for field, value in subject.items():
            if value is not None:
                if type(value) is str and value.strip() != '':
                    setattr(existing, field, value)
                else:
                    setattr(existing, field, value)

        # TODO: Move measurements to relationship bewteen subject and record
        # It does not make sense for this data to be stored here. (Unless we
        # update what data a measurement encodes.)
        for measurement in measurements:
            existing.measurements.add(
                Measurement.updateOrInsert(
                    session,
                    measurement,
                    Subject,
                    existing.id
                )
            )

    @classmethod
    def insert(cls, subject, **kwargs):
        """Insert a new subject"""
        measurements = kwargs.get('measurements', [])

        newSubject = Subject(**subject)

        # TODO Remove measurement as per above
        newSubject.measurements = {
            Measurement.insert(m) for m in measurements
        }
        
        return newSubject

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
            logger.debug('Adding first found subject as relation')
            return session.query(Subject)\
                .filter(Subject.authority == subject['authority'])\
                .filter(Subject.subject == subject['subject'])\
                .first()
