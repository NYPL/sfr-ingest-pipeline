import babelfish
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Unicode,
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy

from model.core import Base, Core
from model.measurement import INSTANCE_MEASUREMENTS, Measurement
from model.identifiers import INSTANCE_IDENTIFIERS, Identifier
from model.link import INSTANCE_LINKS
from model.item import Item
from model.agent import Agent


class Instance(Core, Base):
    """Instances describe specific versions (e.g. editions) of a work in the
    FRBR model. Each of these instance can have multiple items and be
    associated with various agents, measurements, links and identifiers."""
    __tablename__ = 'instances'
    id = Column(Integer, primary_key=True)
    title = Column(Unicode, index=True)
    sub_title = Column(Unicode, index=True)
    alt_title = Column(Unicode, index=True)
    pub_place = Column(Unicode, index=True)
    pub_date = Column(Date, index=True)
    edition = Column(Unicode)
    edition_statement = Column(Unicode)
    table_of_contents = Column(Unicode)
    copyright_date = Column(Date, index=True)
    language = Column(String(2), index=True)

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

    def __repr__(self):
        return '<Instance(title={}, edition={}, work={})>'.format(
            self.title,
            self.edition,
            self.work
        )

    @classmethod
    def updateOrInsert(cls, session, instance):
        """Check for existing instance, if found update that instance. If not
        found, create a new record."""
        items = instance.pop('formats', None)
        agents = instance.pop('agents', None)
        identifiers = instance.pop('identifiers', None)
        measurements = instance.pop('measurements', None)
        existing = Identifier.getByIdentifier(Instance, session, identifiers)
        if existing is not None:
            Instance.update(
                session,
                existing,
                instance,
                items=items,
                agents=agents,
                identifiers=identifiers,
                measurements=measurements
            )
            return None

        newInstance = Instance.insert(
            session,
            instance,
            items=items,
            agents=agents,
            identifiers=identifiers,
            measurements=measurements
        )
        return newInstance

    @classmethod
    def update(cls, session, existing, instance, **kwargs):
        """Update an existing instance"""
        identifiers = kwargs.get('identifiers', [])
        measurements = kwargs.get('measurements', [])
        items = kwargs.get('items', [])
        agents = kwargs.get('agents', [])

        if len(instance['language']) != 2:
            lang = babelfish.Language(instance['language'])
            instance['language'] = lang.alpha2

        for field, value in instance.items():
            if(value is not None and value.strip() != ''):
                setattr(existing, field, value)

        for iden in identifiers:

            status, idenRec = Identifier.returnOrInsert(
                session,
                iden,
                Instance,
                existing.id
            )

            if status == 'new':
                existing.identifiers.append(idenRec)

        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            existing.measurements.append(measurementRec)

        for item in items:
            # TODO This should defer and put this into a stream for
            # processing/storage
            Item.createLocalEpub(item, existing.id)
            # itemRec = Item.updateOrInsert(session, item)
            # existing.items.append(itemRec)

        for agent in agents:
            agentRec, roles = Agent.updateOrInsert(session, agent)
            if roles is None:
                roles = ['author']
            for role in roles:
                if AgentInstances.roleExists(session, agentRec, role, Instance, existing.id) is None:
                    AgentInstances(
                        agent=agentRec,
                        work=existing,
                        role=role
                    )

        return existing

    @classmethod
    def insert(cls, session, instanceData, **kwargs):
        """Insert a new instance record"""
        # Check if language codes are too long and convert if necessary
        if len(instanceData['language']) != 2:
            lang = babelfish.Language(instanceData['language'])
            instanceData['language'] = lang.alpha2

        instance = Instance(**instanceData)

        identifiers = kwargs.get('identifiers', [])
        measurements = kwargs.get('measurements', [])
        items = kwargs.get('items', [])
        agents = kwargs.get('agents', [])

        if agents is not None:
            for agent in agents:
                agentRec, roles = Agent.updateOrInsert(session, agent)
                for role in roles:
                    print(agentRec, instance, role)
                    AgentInstances(
                        agent=agentRec,
                        instance=instance,
                        role=role
                    )

        for iden in identifiers:
            idenRec = Identifier.insert(iden)
            instance.identifiers.append(idenRec)

        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            instance.measurements.append(measurementRec)

        # We need to get the ID of the instance to allow for asynchronously
        # storing the ePub file, so instance is added and flushed here
        # TODO evaluate if this is a good idea, or can be handled better elsewhere
        session.add(instance)
        session.flush()

        for item in items:
            Item.createLocalEpub(item, instance.id)
            # itemRec = Item.updateOrInsert(session, item)
            # instance.items.append(itemRec)

        return instance


class AgentInstances(Core, Base):
    """Table relating agents and instances. Is instantiated as a class to
    allow the assigning of a 'role' to each relationship.
    (e.g. author, editor)"""

    __tablename__ = 'agent_instances'
    instance_id = Column(Integer, ForeignKey('instances.id'), primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), primary_key=True)
    role = Column(String(64))

    instance = relationship(
        Instance,
        backref=backref('agent_instances', cascade='all, delete-orphan')
    )
    agent = relationship('Agent')

    @classmethod
    def roleExists(cls, session, agent, role, model, recordID):
        """Query database to see if relationship with role exists between
        agent and instance. Returns model instance if it does or None if it
        does not"""
        return session.query(cls)\
            .join(Agent)\
            .join(model)\
            .filter(Agent.id == agent.id)\
            .filter(model.id == recordID)\
            .filter(cls.role == role)\
            .one_or_none()
