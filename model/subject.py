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

SUBJECT_WORKS = Table(
    'subject_works', Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id')),
    Column('subject_id', Integer, ForeignKey('subjects.id')),
    Column('weight', Float)
)


class Subject(Core, Base):

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

        measurements = subject.pop('measurements', None)

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

        measurements = kwargs.get('measurements', [])

        for field, value in subject.items():
            if(value is not None and value.strip() != ''):
                setattr(existing, field, value)

        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            existing.measurements.append(measurementRec)

        return existing

    @classmethod
    def insert(cls, subject, **kwargs):

        measurements = kwargs.get('measurements', [])

        newSubject = Subject(**subject)

        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            newSubject.measurements.append(measurementRec)

        return newSubject

    @classmethod
    def lookupSubject(cls, session, subject):
        sbjs = session.query(Subject)\
            .filter(Subject.authority == subject['authority'])\
            .filter(Subject.subject == subject['subject'])\
            .all()
        if len(sbjs) == 1:
            return sbjs[0]
        elif len(sbjs) > 1:
            print('Too many subjects found, should only be one!')
            raise

        # TODO Implement matching based on jaro_winkler scores
        # Will probably need to make this a raw SQL query
        return None
