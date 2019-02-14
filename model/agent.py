from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Unicode,
    or_
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import text
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.associationproxy import association_proxy

from model.core import Base, Core
from model.link import AGENT_LINKS, Link
from model.date import AGENT_DATES, DateField

from helpers.logHelpers import createLog

logger = createLog('agentModel')


class Agent(Core, Base):
    """An agent records an individual, organization, or family that is
    associated with the production of a FRBR entity (work, instance or item).
    Agents may be associated with one or more of these entities and can have
    multiple aliases and links (generally to Wikipedia or other reference
    sources).

    Agents are uniquely identifier by the VIAF and LCNAF authorities, though
    not all agents will have this data. Attempts to merge agents lacking
    authority control is made at the time of import."""

    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, index=True)
    sort_name = Column(Unicode, index=True)
    lcnaf = Column(String(25))
    viaf = Column(String(25))
    biography = Column(Unicode)

    aliases = relationship(
        'Alias',
        back_populates='agent'
    )
    links = relationship(
        'Link',
        secondary=AGENT_LINKS,
        back_populates='agents'
    )
    dates = relationship(
        'DateField',
        secondary=AGENT_DATES,
        back_populates='agents'
    )

    works = relationship(
        'AgentWorks',
        back_populates='agent'
    )

    instances = relationship(
        'AgentInstances',
        back_populates='agent'
    )

    items = relationship(
        'AgentItems',
        back_populates='agent'
    )

    def __repr__(self):
        return '<Agent(name={}, sort_name={}, lcnaf={}, viaf={})>'.format(
            self.name,
            self.sort_name,
            self.lcnaf,
            self.viaf
        )
    
    def __dir__(self):
        return ['name', 'sort_name', 'lcnaf', 'viaf', 'biography']
    
    def getRelationship(self, relRec):
        pass


class Alias(Core, Base):
    """Alternate, or variant names for an agent."""
    __tablename__ = 'aliases'
    id = Column(Integer, primary_key=True)
    alias = Column(Unicode, index=True)
    agent_id = Column(Integer, ForeignKey('agents.id'))

    agent = relationship('Agent', back_populates='aliases')

    def __repr__(self):
        return '<Alias(alias={}, agent={})>'.format(self.alias, self.agent)

