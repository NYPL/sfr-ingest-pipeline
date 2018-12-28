import uuid
from sqlalchemy import (
    Column,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Unicode,
    DateTime,
    Table,
    Float
)
from sqlalchemy.orm import relationship

from model.core import Base, Core

WORK_MEASUREMENTS = Table('work_measurements', Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id')),
    Column('measurement_id', Integer, ForeignKey('measurements.id'))
)

INSTANCE_MEASUREMENTS = Table('instance_measurements', Base.metadata,
    Column('instance_id', Integer, ForeignKey('instances.id')),
    Column('measurement_id', Integer, ForeignKey('measurements.id'))
)

ITEM_MEASUREMENTS = Table('item_measurements', Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id')),
    Column('measurement_id', Integer, ForeignKey('measurements.id'))
)

REPORT_MEASUREMENTS = Table('report_measurements', Base.metadata,
    Column('report_id', Integer, ForeignKey('access_reports.id')),
    Column('measurement_id', Integer, ForeignKey('measurements.id'))
)

SUBJECT_MEASUREMENTS = Table('subject_measurements', Base.metadata,
    Column('subject_id', Integer, ForeignKey('subjects.id')),
    Column('measurement_id', Integer, ForeignKey('measurements.id'))
)

class Measurement(Core, Base):

    __tablename__ = 'measurements'
    id = Column(Integer, primary_key=True)
    quantity = Column(Unicode, index=True)
    value = Column(Float, index=True)
    weight = Column(Float)
    taken_at = Column(DateTime)

    work = relationship('Work', secondary=WORK_MEASUREMENTS, back_populates='measurements')
    instance = relationship('Instance', secondary=INSTANCE_MEASUREMENTS, back_populates='measurements')
    item = relationship('Item', secondary=ITEM_MEASUREMENTS, back_populates='measurements')
    report = relationship('AccessReport', secondary=REPORT_MEASUREMENTS, back_populates='measurements')
    subject = relationship('Subject', secondary=SUBJECT_MEASUREMENTS, back_populates='measurements')


    def __repr__(self):
        return '<Measurement(quantity={}, value={})>'.format(self.quantity, self.value)

    @classmethod
    def updateOrInsert(cls, session, measure, workID):

        existingMeasure = Subject.lookupMeasure(session, measure, workID)

        if existingMeasure is not None:
            updated = Measurement.update(session, measure, existingMeasure)
            return 'update', updated

        return 'insert', Measurement.insert(measure)


    @classmethod
    def insert(cls, measure):
        return Measurement(**measure)


    @classmethod
    def update(cls, measure, existing):
        for field in ['value', 'weight', 'taken_at']:
            if measure[field] is not None:
                existing[field] = measure[field]

        return existing


    @classmethod
    def lookupMeasure(cls, session, measure, workID):
        meas = session.query(Measurement)\
            .join(Measurement.work)\
            .filter(Measurement.quantity == measure.quantity)\
            .filter(Measurement.work.id == workID)\
            .all()
        if len(meas) == 1:
            return meas[0]
        elif len(meas) > 1:
            print("Too many mesurements found, should only be one!")
            raise

        return None
