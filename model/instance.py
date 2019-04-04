
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
        back_populates='instance',
        collection_class=set
    )
    agents = association_proxy(
        'agent_instances',
        'agent'
    )
    measurements = relationship(
        'Measurement',
        secondary=INSTANCE_MEASUREMENTS,
        back_populates='instance',
        collection_class=set
    )
    identifiers = relationship(
        'Identifier',
        secondary=INSTANCE_IDENTIFIERS,
        back_populates='instance',
        collection_class=set
    )
    links = relationship(
        'Link',
        secondary=INSTANCE_LINKS,
        back_populates='instances',
        collection_class=set
    )
    
    alt_titles = relationship(
        'AltTitle',
        secondary=INSTANCE_ALTS,
        back_populates='instance',
        collection_class=set
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
    def updateOrInsert(cls, session, instance, work=None):
        """Check for existing instance, if found update that instance. If not
        found, create a new record."""

        # Check for a matching instance by identifiers (and volume if present)
        existingID = Instance.lookupInstance(
            session,
            instance['identifiers'],
            instance.get('volume', None)    
        )
        if existingID is not None:
            outInstance = session.query(Instance).get(existingID)
            
            parentWork = outInstance.work
            if parentWork is None and work is not None:
                existing.work = work
            
            Instance.update(session, outInstance, instance)
        else:
            outInstance = Instance.insert(session, instance)
        
        return outInstance

    @classmethod
    def lookupInstance(cls, session, identifiers, volume):
        """Query for an existing instance. Generally this will be returned
        by a simple identifier match, but if we have volume data, check to
        be sure that these are the same volume (generally only for) periodicals
        """
        existingID = Identifier.getByIdentifier(Instance, session, identifiers)
        if existingID is not None and volume is not None:
            logger.debug('Checking to see if volume records match')
            existingVol = session.query(Instance.volume).filter(Instance.id == existingID).one_or_none()
            if existingVol[0] != volume:
                logger.debug('Found')
                existingID = None

        return existingID

    @classmethod
    def update(cls, session, existing, instance):
        """Update an existing instance"""
        
        childFields = Instance._buildChildDict(instance)
        childFields['items'] = childFields.pop('formats', [])

        # Get fields targeted for works
        series = instance.pop('series', None)
        seriesPos = instance.pop('series_position', None)
        subjects = instance.pop('subjects', [])
        if existing.work is not None:
            existing.work.updateFields(**{
                'series': series,
                'series_position': seriesPos
            })
            existing.work.importSubjects(session, subjects)

        for field, value in instance.items():
            if(value is not None):
                setattr(existing, field, value)

        Instance._addAgents(session, existing, childFields['agents'])

        Instance._addIdentifiers(session, existing, childFields['identifiers'])

        Instance._addLanguages(session, existing, childFields['language'])

        Instance._addItems(session, existing, childFields['items'])

        Instance._addAltTitles(session, existing, childFields['alt_titles'])

        for m in childFields['measurements']:
            existing.measurements.add(
                Measurement.updateOrInsert(session, m, Instance, existing.id)
            )
        
        for d in childFields['dates']:
            existing.dates.add(
                DateField.updateOrInsert(session, d, Instance, existing.id)
            )

        for l in childFields['links']:
            existing.links.add(
                Link.updateOrInsert(session, l, Instance, existing.id)
            )
        
        for r in childFields['rights']:
            existing.rights.add(
                Rights.updateOrInsert(session, r, Instance, existing.id)
            )

    @classmethod
    def insert(cls, session, instanceData):
        """Insert a new instance record"""
        logger.info('Inserting new instance record')

        childFields = Instance._buildChildDict(instanceData)
        childFields['items'] = childFields.pop('formats', [])

        # Get fields targeted for works
        series = instanceData.pop('series', None)
        seriesPos = instanceData.pop('series_position', None)
        subjects = instanceData.pop('subjects', [])

        instance = Instance(**instanceData)

        for agent in childFields['agents']:
            try:
                agentRec, roles = Agent.updateOrInsert(session, agent)
                for role in roles:
                    AgentInstances(
                        agent=agentRec,
                        instance=instance,
                        role=role
                    )
            except DataError:
                logger.warning('Unable to read agent {}'.format(agent['name']))

        instance.identifiers = {
            Identifier.returnOrInsert(session, i) 
            for i in childFields['identifiers']
        }

        instance.alt_titles = {
            AltTitle(title=a) for a in childFields['alt_titles']
        }

        instance.measurements = {
            Measurement.insert(m) 
            for m in childFields['measurements']
        }

        instance.links = { Link(**l) for l in childFields['links'] }

        instance.dates = { DateField.insert(d) for d in childFields['dates'] }

        instance.rights = {
            Rights.insert(r, dates=r.pop('dates', []))
            for r in childFields['rights']
        }
        
        Instance._addLanguages(session, instance, childFields['language'])

        Instance._addItems(session, instance, childFields['items'])

        logger.info('Inserted {}'.format(instance))
        return instance
    
    @classmethod
    def _addAgents(cls, session, instance, agents):
        for agent in agents:
            try:
                agentRec, roles = Agent.updateOrInsert(session, agent)
                if roles is None:
                    roles = ['author']
                for role in roles:
                    if AgentInstances.roleExists(session, agentRec, role, instance.id) is None:
                        AgentInstances(
                            agent=agentRec,
                            instance=instance,
                            role=role
                        )
            except DataError:
                logger.warning('Unable to read agent {}'.format(agent['name']))
    
    @classmethod
    def _addIdentifiers(cls, session, instance, identifiers):
        for iden in identifiers:
            try:
                instance.identifiers.add(
                    Identifier.returnOrInsert(session, iden)
                )
            except DataError as err:
                logger.warning('Received invalid identifier')
                logger.debug(err)
    
    @classmethod
    def _addLanguages(cls, session, instance, languages):
        if languages is not None:
            if isinstance(languages, str):
                languages = [languages]

            for lang in languages:
                try:
                    instance.language.add(
                        Language.updateOrInsert(session, lang)
                    )
                except DataError:
                    logger.warning('Unable to parse language {}'.format(lang))
    
    @classmethod
    def _addItems(cls, session, instance, items):
        for item in items:
            # Check if the provided record contains an epub that can be stored
            # locally. If it does, defer insert to epub creation process
            instance.items.add(Item.updateOrInsert(session, item))
    
    @classmethod
    def _addAltTitles(cls, session, instance, altTitles):
        for altTitle in list(filter(lambda x: AltTitle.insertOrSkip(session, x, Instance, instance.id), altTitles)):
            instance.alt_titles.append(AltTitle(title=altTitle))


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
