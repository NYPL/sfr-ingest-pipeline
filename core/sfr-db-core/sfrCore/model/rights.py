from sqlalchemy import (
    Table,
    Column,
    Unicode,
    Integer,
    ForeignKey
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import text
from sqlalchemy.orm.exc import NoResultFound

from .core import Base, Core
from .date import DateField, RIGHTS_DATES

from ..helpers import createLog, DBError

logger = createLog('rightsModel')

WORK_RIGHTS = Table(
    'work_rights',
    Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id'), index=True),
    Column('rights_id', Integer, ForeignKey('rights.id'), index=True)
)

INSTANCE_RIGHTS = Table(
    'instance_rights',
    Base.metadata,
    Column('instance_id', Integer, ForeignKey('instances.id'), index=True),
    Column('rights_id', Integer, ForeignKey('rights.id'), index=True)
)

ITEM_RIGHTS = Table(
    'item_rights',
    Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id'), index=True),
    Column('rights_id', Integer, ForeignKey('rights.id'), index=True)
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
    source = Column(Unicode, index=True)
    license = Column(Unicode, index=True)
    rights_statement = Column(Unicode)
    rights_reason = Column(Unicode)

    works = relationship(
        'Work',
        secondary=WORK_RIGHTS,
        backref=backref('rights', collection_class=set)
    )
    instances = relationship(
        'Instance',
        secondary=INSTANCE_RIGHTS,
        backref=backref('rights', collection_class=set)
    )
    items = relationship(
        'Item',
        secondary=ITEM_RIGHTS,
        backref=backref('rights', collection_class=set)
    )

    def __repr__(self):
        return '<Rights(source={}, license={})>'.format(
            self.source,
            self.license
        )

    @classmethod
    def updateOrInsert(cls, session, rights, model, recordID):
        """Query the database for rights from the provided source on the
        current record. If found, update the existing date, if not, insert new
        row"""

        logger.debug('Inserting or updating rights {} on record {}'.format(
            rights['license'],
            recordID
        ))
        
        dates = rights.pop('dates', None)

        outRights = Rights.lookupRights(session, rights, model, recordID)
        if outRights is None:
            logger.info('Inserting new rights object on {}'.format(model))
            outRights = Rights.insert(rights, dates)
        else:
            logger.info('Updating existing rights record {}'.format(
                outRights.id
            ))
            outRights.update(session, rights, dates)

        return outRights

    def update(self, session, rights, dates):
        """Update fields on existing rights assessment"""

        for field, value in rights.items():
            if(
                value is not None
                and value.strip() != ''
            ):
                setattr(self, field, value)
        
        for date in dates:
            self.dates.add(
                DateField.updateOrInsert(session, date, Rights, self.id)
            )

    @classmethod
    def insert(cls, rightsData, dates):
        """Insert a new rights row"""

        rights = Rights()

        for field, value in rightsData.items():
            setattr(rights, field, value)
        
        rights.dates = { DateField.insert(d) for d in dates }

        return rights

    @classmethod
    def lookupRights(cls, session, rights, model, recordID):
        """Query database for link related to current record. Return link
        if found, otherwise return None"""
        return session.query(cls)\
            .join(model.__tablename__)\
            .filter(model.id == recordID)\
            .filter(cls.source == rights['source'])\
            .one_or_none()
