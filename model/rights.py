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
from model.date import DateField, RIGHTS_DATES

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
    source = Column(Unicode, index=True)
    license = Column(Unicode, index=True)
    rights_statement = Column(Unicode, index=True)
    rights_reason = Column(Unicode, index=True)

    works = relationship(
        'Work',
        secondary=WORK_RIGHTS,
        backref='rights'
    )
    instances = relationship(
        'Instance',
        secondary=INSTANCE_RIGHTS,
        backref='rights'
    )
    items = relationship(
        'Item',
        secondary=ITEM_RIGHTS,
        backref='rights'
    )

    def __repr__(self):
        return '<Rights(source={}, license={})>'.format(
            self.source,
            self.license
        )
    
    def __dir__(self):
        return ['source', 'license', 'rights_statement', 'rights_reason']
