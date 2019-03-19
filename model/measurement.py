from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Unicode,
    DateTime,
    Table,
    Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import MultipleResultsFound

from model.core import Base, Core

from helpers.logHelpers import createLog
from helpers.errorHelpers import DBError, DataError

logger = createLog('measurements')

WORK_MEASUREMENTS = Table(
    'work_measurements',
    Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id')),
    Column('measurement_id', Integer, ForeignKey('measurements.id'))
)

INSTANCE_MEASUREMENTS = Table(
    'instance_measurements',
    Base.metadata,
    Column('instance_id', Integer, ForeignKey('instances.id')),
    Column('measurement_id', Integer, ForeignKey('measurements.id'))
)

ITEM_MEASUREMENTS = Table(
    'item_measurements',
    Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id')),
    Column('measurement_id', Integer, ForeignKey('measurements.id'))
)

REPORT_MEASUREMENTS = Table(
    'report_measurements',
    Base.metadata,
    Column('report_id', Integer, ForeignKey('access_reports.id')),
    Column('measurement_id', Integer, ForeignKey('measurements.id'))
)

SUBJECT_MEASUREMENTS = Table(
    'subject_measurements',
    Base.metadata,
    Column('subject_id', Integer, ForeignKey('subjects.id')),
    Column('measurement_id', Integer, ForeignKey('measurements.id'))
)


class Measurement(Core, Base):
    """A generic table for recording numerical/quantitative data about a
    record. This can include things such as file size and number of library
    holdings for a work"""
    __tablename__ = 'measurements'
    id = Column(Integer, primary_key=True)
    quantity = Column(Unicode, index=True)
    value = Column(Float, index=True)
    weight = Column(Float)
    taken_at = Column(DateTime)
    source_id = Column(Unicode, index=True)

    work = relationship(
        'Work',
        secondary=WORK_MEASUREMENTS,
        back_populates='measurements'
    )
    instance = relationship(
        'Instance',
        secondary=INSTANCE_MEASUREMENTS,
        back_populates='measurements'
    )
    item = relationship(
        'Item',
        secondary=ITEM_MEASUREMENTS,
        back_populates='measurements'
    )
    report = relationship(
        'AccessReport',
        secondary=REPORT_MEASUREMENTS,
        back_populates='measurements'
    )
    subject = relationship(
        'Subject',
        secondary=SUBJECT_MEASUREMENTS,
        back_populates='measurements'
    )

    def __repr__(self):
        return '<Measurement(quantity={}, value={})>'.format(
            self.quantity,
            self.value
        )

    @classmethod
    def updateOrInsert(cls, session, measure, model, recordID):

        existingMeasure = Measurement.lookupMeasure(
            session,
            measure,
            model,
            recordID
        )

        if existingMeasure is not None:
            updated = Measurement.update(measure, existingMeasure)
            return 'update', updated

        return 'insert', Measurement.insert(measure)

    @classmethod
    def insert(cls, measure):
        return Measurement(**measure)

    @classmethod
    def update(cls, measure, existing):
        for field in ['value', 'weight', 'taken_at']:
            if measure[field] is not None:
                setattr(existing, field, measure[field])

        return existing

    @classmethod
    def lookupMeasure(cls, session, measure, model, recordID):
        try:
            return session.query(cls)\
                .join(model.__tablename__[:-1])\
                .filter(cls.quantity == measure.quantity)\
                .filter(cls.source_id, measure.source_id)\
                .filter(model.id == recordID)\
                .one_or_none()
        except MultipleResultsFound:
            logger.error('Found duplicate measurement entries for {} {}'.format(
                model.__tablename__,
                recordID
            ))
            raise DataError('Duplicate measurement entries')
    
    @classmethod
    def getMeasurements(cls, session, measure, model, recordID):
        return session.query(cls.value)\
            .join(model.__tablename__[:-1])\
            .filter(cls.quantity == measure)\
            .filter(model.id == recordID)\
            .all()

