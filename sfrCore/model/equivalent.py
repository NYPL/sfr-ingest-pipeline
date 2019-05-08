from sqlalchemy import (
    Table,
    Column,
    Unicode,
    Integer,
    JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
from sqlalchemy.orm.exc import NoResultFound

from sfrCore.model.core import Base, Core
from sfrCore.model.date import DateField, RIGHTS_DATES

from sfrCore.helpers.errors import DBError
from sfrCore.helpers.logger import createLog

logger = createLog('equivalentTable')


class Equivalent(Core, Base):
    """A table that stores potential equivalent records (generally work/work or
    instance/instance) records. This data can be used later to merge records
    either manually or programatically and includes the data used to originally
    make the equivalent assertion.

    @value source_id -- originating record to be made equivalent to
    @value target_id -- target read to possibly be equivalent/merged
    @value type -- the type of records 
    @value match_data -- the block of JSON data that describes how the assertion
    was made
    """

    __tablename__ = 'equivalency'
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, index=True, nullable=False)
    target_id = Column(Integer, index=True, nullable=False)
    type = Column(Unicode, index=True)
    match_data = Column(JSON)

    def __repr__(self):
        return '<Equivalency(source={}, target={}, type={})>'.format(
            self.source_id,
            self.target_id,
            self.type
        )

    @classmethod
    def addEquivalencies(cls, session, topMatch, matches, table, matchData):
        for match in matches:
            session.add(Equivalent.createEquivalency(
                topMatch,
                match[0],
                table,
                matchData
            ))

    @classmethod
    def createEquivalency(cls, sourceID, targetID, table, matchData):
        """Create an equivalency entry for two possibly matching entries"""

        logger.debug('Creating equivalency on {} between {} and {}'.format(
            table,
            sourceID,
            targetID
        ))
        
        return Equivalent(
            source_id=sourceID,
            target_id=targetID,
            type=table,
            match_data=matchData
        )
