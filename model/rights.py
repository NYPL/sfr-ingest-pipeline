from sqlalchemy import (
    Table,
    Column,
    Unicode,
    Integer,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
from sqlalchemy.orm.exc import NoResultFound

from model.core import Base, Core

from helpers.errorHelpers import DBError
from helpers.logHelpers import createLog

logger = createLog('rightsModel')

WORK_RIGHTS = Table(
    'work_rights',
    Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id')),
    Column('rights_id', Integer, ForeignKey('rights.id'))
)

INSTANCE_RIGHTS = Table(
    'instance_rights',
    Base.metadata,
    Column('instance_id', Integer, ForeignKey('instances.id')),
    Column('rights_id', Integer, ForeignKey('rights.id'))
)

ITEM_RIGHTS = Table(
    'item_rights',
    Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id')),
    Column('rights_id', Integer, ForeignKey('rights.id'))
)


class Rights(Core, Base):
    """An abstract class that represents a rights assessment. This can apply
    to any level in the SFR metadata model, and should include a resolvable
    URI and a human readable component, though the URI is not strictly 
    required. Additionally a rationale for the assessment can be provided

    @value source -- institution/individual that has made the assessment
    @value license -- string (preferably URI) that defines the assigned rights
    @value rights_statement -- human readable version of the rights assessment
    @value rights_reason -- a justification for the rights statement
    @value dates -- list of dates associated with the rights assessment
    """

    __tablename__ = 'rights'
    id = Column(Integer, primary_key=True)
    license = Column(Unicode, index=True)
    rights_statement = Column(Unicode, index=True)
    rights_reason = Column(Unicode, index=True)

    works = relationship(
        'Work',
        secondary=WORK_DATES,
        back_populates='dates'
    )
    instances = relationship(
        'Instance',
        secondary=INSTANCE_DATES,
        back_populates='dates'
    )
    items = relationship(
        'Item',
        secondary=ITEM_DATES,
        back_populates='dates'
    )
    dates = relationship(
        'Date',
        secondary=RIGHTS_DATES,
        back_populates='dates'
    )

    def __repr__(self):
        return '<Rights(source={}, license={})>'.format(
            self.source,
            self.license
        )

    @classmethod
    def updateOrInsert(cls, session, rights, model, recordID):
        logger.debug('Inserting or updating rights {} on record {}'.format(
            rights['license'],
            recordID
        ))
        """Query the database for rights from the provided source on the
        current record. If found, update the existing date, if not, insert new
        row"""
        existing = Rights.lookupRights(session, rights, model, recordID)
        if existing is not None:
            logger.info('Updating existing rights record {}'.format(
                existing.id
            ))
            Rights.update(existing, date)
            return None

        logger.info('Inserting new date object')
        return Rights.insert(date)

    @classmethod
    def update(cls, existing, rights):
        """Update fields on existing rights assessment"""
        for field, value in rights.items():
            if(
                value is not None
                and value.strip() != ''
            ):
                setattr(existing, field, value)

    @classmethod
    def insert(cls, rightsData):
        """Insert a new rights row"""
        rights = Rights()
        for field, value in rightsData.items():
            setattr(rights, field, value)

        return rights

    @classmethod
    def lookupRights(cls, session, rights, model, recordID):
        """Query database for link related to current record. Return link
        if found, otherwise return None"""
        return session.query(cls)\
            .join(model.__tablename__)\
            .filter(model.id == recordID)\
            .filter(cls.source == date['source'])\
            .one_or_none()
