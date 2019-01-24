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

    @classmethod
    def updateOrInsert(cls, session, subject):
        """Query for an existing subject, and if found, update existing record,
        otherwise insert a new subject"""
        measurements = subject.pop('measurements', [])

        existingSubject = Subject.lookupSubject(session, subject)

        if existingSubject is not None:
            return 'update', Subject.update(
                existingSubject,
                subject,
                measurements=measurements
            )

        return 'insert', Subject.insert(
            subject,
            measurements=measurements
        )

    @classmethod
    def update(cls, existing, subject, **kwargs):
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
            measurementRec = Measurement.insert(measurement)
            existing.measurements.append(measurementRec)

        return existing

    @classmethod
    def insert(cls, subject, **kwargs):
        """Insert a new subject"""
        measurements = kwargs.get('measurements', [])

        newSubject = Subject(**subject)

        # TODO Remove measurement as per above
        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            newSubject.measurements.append(measurementRec)

        return newSubject

    @classmethod
    def lookupSubject(cls, session, subject):
        """Query database for an existing subject. If multiple are found,
        raise an error, otherwise return the subject record."""
        sbjs = session.query(Subject)\
            .filter(Subject.authority == subject['authority'])\
            .filter(Subject.subject == subject['subject'])\
            .all()
        if len(sbjs) == 1:
            return sbjs[0]
        elif len(sbjs) > 1:
            logger.error('Too many subjects found for {}'.format(
                subject['subject']
            ))
            raise DBError('subjects', 'Found multiple subject entries')

        # TODO Implement matching based on jaro_winkler scores
        # Will probably need to make this a raw SQL query
        return None
