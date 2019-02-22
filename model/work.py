import uuid
import json
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Unicode,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.exc import NoResultFound

from model.core import Base, Core
from model.subject import SUBJECT_WORKS
from model.identifiers import WORK_IDENTIFIERS, Identifier
from model.altTitle import AltTitle, WORK_ALTS
from model.rawData import RawData
from model.measurement import WORK_MEASUREMENTS, Measurement
from model.link import WORK_LINKS, Link
from model.date import WORK_DATES, DateField
from model.instance import Instance
from model.agent import Agent
from model.subject import Subject

from helpers.errorHelpers import DBError
from helpers.logHelpers import createLog

logger = createLog('workModel')


#
# The root-level SFR record of Work corresponds to the FRBR and BIBFRAME
# concepts at the same level.
#
class Work(Core, Base):
    """The highest level FRBR entity, a work encodes the data about the
    intellectual content of an entity. This includes things such as title,
    author and, importantly, copyright data. The work also includes
    relationships to agents, instances, alternate titles, links and
    measurements"""
    __tablename__ = 'works'
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False)
    title = Column(Unicode, index=True)
    sort_title = Column(Unicode, index=True)
    sub_title = Column(Unicode, index=True)
    medium = Column(Unicode)
    series = Column(Unicode)
    series_position = Column(Integer)
    summary = Column(Unicode)

    #
    # Relationships
    #

    alt_titles = relationship(
        'AltTitle',
        secondary=WORK_ALTS,
        back_populates='work'
    )
    subjects = relationship(
        'Subject',
        secondary=SUBJECT_WORKS,
        back_populates='work'
    )
    instances = relationship(
        'Instance',
        back_populates='work'
    )
    agents = relationship(
        'AgentWorks',
        back_populates='work'
    )
    measurements = relationship(
        'Measurement',
        secondary=WORK_MEASUREMENTS,
        back_populates='work'
    )
    identifiers = relationship(
        'Identifier',
        secondary=WORK_IDENTIFIERS,
        back_populates='work'
    )
    links = relationship(
        'Link',
        secondary=WORK_LINKS,
        back_populates='works'
    )
    dates = relationship(
        'DateField',
        secondary=WORK_DATES,
        back_populates='works'
    )
    import_json = relationship(
        'RawData',
        back_populates='work'
    )

    def __repr__(self):
        return '<Work(title={})>'.format(self.title)
    
    def __dir__(self):
        return ['uuid', 'title', 'sort_title', 'sub_title', 'language', 'license', 'rights_statement', 'medium', 'series', 'series_position', 'date_modified', 'date_updated']

class AgentWorks(Core, Base):
    """Table relating agents and works. Is instantiated as a class to
    allow the assigning of a 'role' to each relationship.
    (e.g. author, editor)"""

    __tablename__ = 'agent_works'
    work_id = Column(Integer, ForeignKey('works.id'), primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), primary_key=True)
    role = Column(String(64))

    work = relationship(
        Work,
        backref=backref('agent_works', cascade='all, delete-orphan')
    )
    agent = relationship(
        'Agent',
        backref=backref('agent_works')
    )

    def __repr__(self):
        return '<AgentWorks(work={}, agent={}, role={})>'.format(
            self.work_id,
            self.agent_id,
            self.role
        )
