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

SUBJECT_WORKS = Table('subject_works', Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id')),
    Column('subject_id', Integer, ForeignKey('subjects.id')),
    Column('weight', Float)
)


class Subject(Core, Base):

    __tablename__= 'subjects'
    id = Column(Integer, primary_key=True)
    authority = Column(Unicode)
    uri = Column(String(50))
    subject = Column(Unicode, index=True)
    weight = Column(Float)

    work = relationship('Work', secondary=SUBJECT_WORKS, back_populates='subjects')

    def __repr__(self):
        return '<Subject(subject={}, uri={}, authority={})'.format(self.subject, self.uri, self.authority)


    @classmethod
    def updateOrInsert(cls, session, subject):

        existingSubject = Subject.lookupSubject(session, subject)

        if existingSubject is not None:
            return 'update', Subject.update(session, existingSubject, subject)

        return 'insert', Subject.insert(subject)


    @classmethod
    def update(cls, existing, subject):
        for field, value in subject.items():
            if(value is not None and value.strip() != ''):
                setField = getattr(existing, field)
                setField = value


    @classmethod
    def insert(cls, subject):
        return Subject(**subject)

    @classmethod
    def lookupSubject(cls, session, subject):
        sbjs = session.query(Subject)\
            .filter(Subject.authority == subject.authority)\
            .filter(Subject.subject == subject.subject)\
            .all()
        if len(sbjs) == 1:
            return sbjs[0]
        elif len(sbjs) > 1:
            print("Too many subjects found, should only be one!")
            raise

        # TODO Implement matching based on jaro_winkler scores
        # Will probably need to make this a raw SQL query
        return None
