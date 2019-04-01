
import re
from datetime import datetime
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Unicode,
    PrimaryKeyConstraint
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy

from model.core import Base, Core
from model.measurement import INSTANCE_MEASUREMENTS, Measurement
from model.identifiers import INSTANCE_IDENTIFIERS, Identifier
from model.link import INSTANCE_LINKS, Link
from model.date import INSTANCE_DATES, DateField
from model.item import Item
from model.agent import Agent
from model.altTitle import INSTANCE_ALTS, AltTitle
from model.rights import Rights, INSTANCE_RIGHTS
from model.language import Language

from helpers.logHelpers import createLog
from helpers.errorHelpers import DataError

logger = createLog('instances')


class Instance(Core, Base):
    """Instances describe specific versions (e.g. editions) of a work in the
    FRBR model. Each of these instance can have multiple items and be
    associated with various agents, measurements, links and identifiers."""
    __tablename__ = 'instances'
    id = Column(Integer, primary_key=True)
    title = Column(Unicode, index=True)
    sub_title = Column(Unicode, index=True)
    pub_place = Column(Unicode, index=True)
    edition = Column(Unicode)
    edition_statement = Column(Unicode)
    volume = Column(Unicode, index=True)
    table_of_contents = Column(Unicode)
    copyright_date = Column(Date, index=True)
    extent = Column(Unicode)
    
    work_id = Column(Integer, ForeignKey('works.id'))

    work = relationship(
        'Work',
        back_populates='instances'
    )
    items = relationship(
        'Item',
        back_populates='instance'
    )
    agents = association_proxy(
        'agent_instances',
        'agent'
    )
    measurements = relationship(
        'Measurement',
        secondary=INSTANCE_MEASUREMENTS,
        back_populates='instance'
    )
    identifiers = relationship(
        'Identifier',
        secondary=INSTANCE_IDENTIFIERS,
        back_populates='instance'
    )
    links = relationship(
        'Link',
        secondary=INSTANCE_LINKS,
        back_populates='instances'
    )
    
    alt_titles = relationship(
        'AltTitle',
        secondary=INSTANCE_ALTS,
        back_populates='instance'
    )

    CHILD_FIELDS = [
        'formats',
        'agents',
        'identifiers',
        'measurements',
        'dates',
        'links',
        'alt_titles',
        'rights',
        'language'
    ]

    def __repr__(self):
        return '<Instance(title={}, edition={}, work={})>'.format(
            self.title,
            self.edition,
            self.work
        )

    @classmethod
    def _buildChildDict(cls, instData):
        return { field: instData.pop(field, []) for field in cls.CHILD_FIELDS }

    @classmethod
    def insert(cls, session, instanceData):
        """Insert a new instance record"""
        logger.info('Inserting new instance record {}'.format(
            instanceData['title']
        ))

        childFields = Instance._buildChildDict(instanceData)
        childFields['items'] = childFields.pop('formats', [])

        # Remove fields intended for works (These should not be found here)
        instanceData.pop('series', None)
        instanceData.pop('series_position', None)
        instanceData.pop('subjects', [])

        instance = Instance(**instanceData)
        session.add(instance)

        Instance._addIdentifiers(session, instance, childFields['identifiers'])

        Instance._addAgents(session, instance, childFields['agents'])

        Instance._addAltTitles(instance, childFields['alt_titles'])

        Instance._addMeasurements(session, instance, childFields['measurements'])

        Instance._addLinks(instance, childFields['links'])

        Instance._addDates(instance, childFields['dates'])

        Instance._addLanguages(session, instance, childFields['language'])

        Instance._addRights(instance, childFields['rights'])

        Instance._addItems(session, instance, childFields['items'])

        logger.info('Inserted {}'.format(instance))
        return instance

    @classmethod
    def _addIdentifiers(cls, session, instance, identifiers):
        for iden in identifiers:
            try:
                status, idenRec = Identifier.returnOrInsert(
                    session,
                    iden
                )
                instance.identifiers.append(idenRec)
            except DataError as err:
                logger.warning('Received invalid identifier')
                logger.debug(err)
    
    @classmethod
    def _addAgents(cls, session, instance, agents):
        relsCreated = []
        for agent in agents:
            try:
                agentRec, roles = Agent.updateOrInsert(session, agent)
                for role in roles:
                    if (agentRec.name, role) in relsCreated: continue
                    relsCreated.append((agentRec.name, role))
                    AgentInstances(
                        agent=agentRec,
                        instance=instance,
                        role=role
                    )
            except DataError:
                logger.warning('Unable to read agent {}'.format(agent['name']))
    
    @classmethod
    def _addAltTitles(cls, instance, altTitles):
        if altTitles is not None:
            # Quick conversion to set to eliminate duplicate alternate titles
            for altTitle in list(set(altTitles)):
                instance.alt_titles.append(AltTitle(title=altTitle))

    @classmethod
    def _addMeasurements(cls, session, instance, measurements):
        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            instance.measurements.append(measurementRec)
    
    @classmethod
    def _addLinks(cls, instance, links):
        for link in links:
            newLink = Link(**link)
            instance.links.append(newLink)
    
    @classmethod
    def _addDates(cls, instance, dates):
        for date in dates:
            newDate = DateField.insert(date)
            instance.dates.append(newDate)
    
    @classmethod
    def _addLanguages(cls, session, instance, languages):
        if languages is not None:
            if isinstance(languages, str):
                languages = [languages]
            
            for lang in languages:
                try:
                    newLang = Language.updateOrInsert(session, lang)
                    instance.language.append(newLang)
                except DataError:
                    logger.debug('Unable to parse language {}'.format(lang))
                    continue
    
    @classmethod
    def _addRights(cls, instance, rights):
        for rightsStmt in rights:
            rightsDates = rightsStmt.pop('dates', [])
            newRights = Rights.insert(rightsStmt, dates=rightsDates)
            instance.rights.append(newRights)
    
    @classmethod
    def _addItems(cls, session, instance, items):
        for item in items:
            itemRec, op = Item.createOrStore(session, item, instance)
            if op == 'inserted':
                instance.items.append(itemRec)
    
    @classmethod
    def addItemRecord(cls, session, instanceID, itemRec):
        instance = session.query(cls).get(instanceID)
        instance.items.append(itemRec)

class AgentInstances(Core, Base):
    """Table relating agents and instances. Is instantiated as a class to
    allow the assigning of a 'role' to each relationship.
    (e.g. author, editor)"""

    __tablename__ = 'agent_instances'
    instance_id = Column(Integer, ForeignKey('instances.id'), primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), primary_key=True)
    role = Column(String(64), primary_key=True)

    agentInstancesPkey = PrimaryKeyConstraint(
        'instance_id',
        'agent_id',
        'role',
        name='agent_instances_pkey'
    )

    instance = relationship(
        Instance,
        backref=backref('agent_instances', cascade='all, delete-orphan')
    )
    agent = relationship('Agent')

    @classmethod
    def roleExists(cls, session, agent, role, recordID):
        """Query database to see if relationship with role exists between
        agent and instance. Returns model instance if it does or None if it
        does not"""
        return session.query(cls)\
            .filter(cls.agent_id == agent.id)\
            .filter(cls.instance_id == recordID)\
            .filter(cls.role == role)\
            .one_or_none()
