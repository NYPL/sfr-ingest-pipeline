import babelfish
import re
from datetime import datetime
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
from model.link import INSTANCE_LINKS, Link
from model.date import INSTANCE_DATES, DateField
from model.item import Item
from model.agent import Agent
from model.altTitle import INSTANCE_ALTS, AltTitle

from helpers.logHelpers import createLog

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
    table_of_contents = Column(Unicode)
    copyright_date = Column(Date, index=True)
    language = Column(String(2), index=True)
    extent = Column(Unicode)
    license = Column(String(255))
    rights_statement = Column(Unicode)

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
    dates = relationship(
        'DateField',
        secondary=INSTANCE_DATES,
        back_populates='instances'
    )
    alt_titles = relationship(
        'AltTitle',
        secondary=INSTANCE_ALTS,
        back_populates='instance'
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
        dates = instance.pop('dates', [])
        links = instance.pop('links', [])
        alt_titles = instance.pop('alt_titles', None)

        # Get fields targeted for works
        series = instance.pop('series', None)
        seriesPos = instance.pop('series_position', None)
        subjects = instance.pop('subjects', [])


        existing = Identifier.getByIdentifier(Instance, session, identifiers)
        if existing is not None:
            parentWork = existing.work
            parentWork.updateFields(**{
                'series': series,
                'series_position': seriesPos
            })
            parentWork.importSubjects(session, subjects)
            Instance.update(
                session,
                existing,
                instance,
                items=items,
                agents=agents,
                identifiers=identifiers,
                measurements=measurements,
                dates=dates,
                links=links,
                alt_titles=alt_titles
            )
            return existing, 'updated'

        newInstance = Instance.insert(
            session,
            instance,
            items=items,
            agents=agents,
            identifiers=identifiers,
            measurements=measurements,
            dates=dates,
            links=links,
            alt_titles=alt_titles
        )
        return newInstance, 'inserted'

    @classmethod
    def update(cls, session, existing, instance, **kwargs):
        """Update an existing instance"""
        identifiers = kwargs.get('identifiers', [])
        measurements = kwargs.get('measurements', [])
        items = kwargs.get('items', [])
        agents = kwargs.get('agents', [])
        altTitles = kwargs.get('alt_titles', [])
        links = kwargs.get('links', [])
        dates = kwargs.get('dates', [])

        if instance['language'] is not None and len(instance['language']) != 2:
            langs = re.split(r'\W+', instance['language'])
            try:
                lang = babelfish.Language(langs[0])
                instance['language'] = lang.alpha2
            except ValueError:
                instance['language'] = None
                logger.warning('Unable to assign language {} to instance {}'.format(langs[0], existing.id))

        for field, value in instance.items():
            if(value is not None):
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

        for date in dates:
            updateDate = DateField.updateOrInsert(session, date, Instance, existing.id)
            if updateDate is not None:
                existing.dates.append(updateDate)

        for item in items:
            # Check if the provided record contains an epub that can be stored
            # locally. If it does, defer insert to epub creation process
            itemRec = Item.createOrStore(session, item, existing.id)
            if itemRec is not None:
                existing.items.append(itemRec)

        for agent in agents:
            agentRec, roles = Agent.updateOrInsert(session, agent)
            if roles is None:
                roles = ['author']
            for role in roles:
                if AgentInstances.roleExists(session, agentRec, role, Instance, existing.id) is None:
                    AgentInstances(
                        agent=agentRec,
                        instance=existing,
                        role=role
                    )

        for altTitle in list(filter(lambda x: AltTitle.insertOrSkip(session, x, Instance, existing.id), altTitles)):
            existing.alt_titles.append(AltTitle(title=altTitle))

        for link in links:
            updateLink = Link.updateOrInsert(session, link, Instance, existing.id)
            if updateLink is not None:
                existing.links.append(updateLink)

        return existing

    @classmethod
    def insert(cls, session, instanceData, **kwargs):
        """Insert a new instance record"""
        # Check if language codes are too long and convert if necessary
        if len(instanceData['language']) != 2:
            langs = re.split(r'\W+', instanceData['language'])
            try:
                lang = babelfish.Language(langs[0])
                instanceData['language'] = lang.alpha2
            except ValueError:
                instanceData['language'] = None
                logger.warning('Unable to assign language {} to new instance'.format(langs[0]))

        instance = Instance(**instanceData)

        identifiers = kwargs.get('identifiers', [])
        measurements = kwargs.get('measurements', [])
        items = kwargs.get('items', [])
        agents = kwargs.get('agents', [])
        altTitles = kwargs.get('alt_titles', [])
        links = kwargs.get('links', [])
        dates = kwargs.get('dates', [])

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

        for altTitle in altTitles:
            instance.alt_titles.append(AltTitle(title=altTitle))

        for link in links:
            newLink = Link(**link)
            instance.links.append(newLink)

        for date in dates:
            newDate = DateField.insert(date)
            instance.dates.append(newDate)

        # We need to get the ID of the instance to allow for asynchronously
        # storing the ePub file, so instance is added and flushed here
        # TODO evaluate if this is a good idea, or can be handled better elsewhere
        session.add(instance)
        session.flush()

        for item in items:
            itemRec = Item.createOrStore(session, item, instance.id)
            if itemRec is not None:
                instance.items.append(itemRec)

        return instance

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
