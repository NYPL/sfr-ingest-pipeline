
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

    def __repr__(self):
        return '<Instance(title={}, edition={}, work={})>'.format(
            self.title,
            self.edition,
            self.work
        )

    @classmethod
    def updateOrInsert(cls, session, instance, work=None):
        """Check for existing instance, if found update that instance. If not
        found, create a new record."""
        items = instance.pop('formats', None)
        agents = instance.pop('agents', None)
        identifiers = instance.pop('identifiers', None)
        measurements = instance.pop('measurements', None)
        dates = instance.pop('dates', [])
        links = instance.pop('links', [])
        alt_titles = instance.pop('alt_titles', None)
        rights = instance.pop('rights', [])
        language = instance.pop('language', [])

        # Get fields targeted for works
        series = instance.pop('series', None)
        seriesPos = instance.pop('series_position', None)
        subjects = instance.pop('subjects', [])

        # Check for a matching instance by identifiers (and volume if present)
        existingID = Instance.lookupInstance(
            session,
            identifiers,
            instance.get('volume', None)    
        )
        if existingID is not None:
            existing = session.query(Instance).get(existingID)
            parentWork = existing.work
            if parentWork is None and work is not None:
                existing.work = work
                parentWork = work
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
                alt_titles=alt_titles,
                rights=rights,
                language=language
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
            alt_titles=alt_titles,
            rights=rights,
            language=language
        )
        return newInstance, 'inserted'

    @classmethod
    def lookupInstance(cls, session, identifiers, volume):
        """Query for an existing instance. Generally this will be returned
        by a simple identifier match, but if we have volume data, check to
        be sure that these are the same volume (generally only for) periodicals
        """
        existingID = Identifier.getByIdentifier(Instance, session, identifiers)
        if existingID is not None and volume is not None:
            existingVol = session.query(Instance.volume).filter(Instance.id == existingID).one_or_none()
            if existingVol != volume:
                existingID = None

        return existingID

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
        rights = kwargs.get('rights', [])
        language = kwargs.get('language', [])

        for field, value in instance.items():
            if(value is not None):
                setattr(existing, field, value)

        for iden in identifiers:
            try:
                status, idenRec = Identifier.returnOrInsert(
                    session,
                    iden,
                    Instance,
                    existing.id
                )
                if status == 'new':
                    existing.identifiers.append(idenRec)
            except DataError as err:
                logger.warning('Received invalid identifier')
                logger.debug(err)

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
            itemRec, op = Item.createOrStore(session, item, existing.id)
            if op == 'inserted':
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
        
        for rightsStmt in rights:
            updateRights = Rights.updateOrInsert(
                session,
                rightsStmt,
                Instance,
                existing.id
            )
            if updateRights is not None:
                existing.rights.append(updateRights)
        
        if isinstance(language, str) or language is None:
            language = [language]

        for lang in language:
            try:
                newLang = Language.updateOrInsert(session, lang)
                langRel = Language.lookupRelLang(session, newLang, Instance, existing)
                if langRel is None:
                    existing.language.append(newLang)
            except DataError:
                logger.warning('Unable to parse language {}'.format(lang))

        return existing

    @classmethod
    def insert(cls, session, instanceData, **kwargs):
        """Insert a new instance record"""
        
        instance = Instance(**instanceData)

        identifiers = kwargs.get('identifiers', [])
        measurements = kwargs.get('measurements', [])
        items = kwargs.get('items', [])
        agents = kwargs.get('agents', [])
        altTitles = kwargs.get('alt_titles', [])
        links = kwargs.get('links', [])
        dates = kwargs.get('dates', [])
        rights = kwargs.get('rights', [])
        language = kwargs.get('language', [])

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
            try:
                instance.identifiers.append(Identifier.insert(iden))
            except DataError as err:
                logger.warning('Received invalid identifier')
                logger.debug(err)

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
        
        for rightsStmt in rights:
            rightsDates = rightsStmt.pop('dates', [])
            newRights = Rights.insert(rightsStmt, dates=rightsDates)
            instance.rights.append(newRights)
        
        if isinstance(language, str) or language is None:
            language = [language]
        
        for lang in language:
            try:
                newLang = Language.updateOrInsert(session, lang)
                instance.language.append(newLang)
            except DataError:
                logger.debug('Unable to parse language {}'.format(lang))
                continue

        # We need to get the ID of the instance to allow for asynchronously
        # storing the ePub file, so instance is added and flushed here
        # TODO evaluate if this is a good idea, or can be handled better elsewhere
        session.add(instance)

        for item in items:
            itemRec, op = Item.createOrStore(session, item, instance.id)
            if op == 'inserted':
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
