import os
import re
from copy import deepcopy
from collections import deque
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Float,
    String,
    Unicode,
    DateTime,
    PrimaryKeyConstraint
)

from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.associationproxy import association_proxy

from .core import Base, Core
from .measurement import (
    ITEM_MEASUREMENTS,
    REPORT_MEASUREMENTS,
    Measurement
)
from .identifiers import ITEM_IDENTIFIERS, Identifier
from .link import ITEM_LINKS, Link
from .date import ITEM_DATES, DateField
from .rights import Rights, ITEM_RIGHTS
from .agent import Agent

from ..helpers import createLog, DataError

logger = createLog('items')


class Item(Core, Base):
    """An item is an individual copy of a work in the FRBR model. In the
    digital realm this refers to a specifically stored copy of the work"""
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    source = Column(Unicode)
    content_type = Column(Unicode)
    modified = Column(DateTime)
    drm = Column(Unicode)
    
    instance_id = Column(Integer, ForeignKey('instances.id'), index=True)

    instance = relationship(
        'Instance',
        back_populates='items'
    )
    measurements = relationship(
        'Measurement',
        secondary=ITEM_MEASUREMENTS,
        back_populates='item',
        collection_class=set
    )
    identifiers = relationship(
        'Identifier',
        secondary=ITEM_IDENTIFIERS,
        back_populates='item',
        collection_class=set
    )
    agents = association_proxy(
        'agent_items',
        'agents'
    )
    access_reports = relationship(
        'AccessReport',
        back_populates='item',
        collection_class=set
    )
    links = relationship(
        'Link',
        secondary=ITEM_LINKS,
        back_populates='items',
        collection_class=set
    )

    RELS = [
        'links',
        'identifiers',
        'measurements',
        'dates',
        'rights',
        'agents'
    ]

    SOURCE_REGEX = {
        'gut': r'gutenberg.org\/ebooks\/[0-9]+\.epub\.(?:no|)images$',
        'ia': r'archive.org\/details\/[a-z0-9]+$'
    }

    EPUB_SOURCES = ['gut']
    
    def __init__(self, session=None):
        self.session = session

    def __repr__(self):
        return '<Item(source={}, instance={})>'.format(
            self.source,
            self.instance
        )

    def createTmpRelations(self, itemData):
        for relType in Item.RELS:
            tmpRel = 'tmp_{}'.format(relType)
            setattr(self, tmpRel, itemData.pop(relType, []))
            if getattr(self, tmpRel) is None: setattr(self, tmpRel, [])
    
    def removeTmpRelations(self):
        """Removes temporary attributes that were used to hold related objects.
        """
        for rel in Item.RELS: delattr(self, 'tmp_{}'.format(rel))
    
    @classmethod
    def createOrStore(cls, session, item, instance):
        links = deque(item.pop('links', []))
        item['links'] = []
        deferredLoad = False
        while len(links) > 0:
            link = links.popleft()
            url = link['url']
            if not isinstance(url, (str,)): continue
            for source, regex in cls.SOURCE_REGEX.items():
                try:
                    if re.search(regex, url):
                        if source in cls.EPUB_SOURCES:
                            # We need to get the ID of the instance to allow 
                            # for asynchronously storing the ePub file, so
                            # instance is added and flushed here
                            if instance.id is None:
                                session.add(instance)
                                session.flush()

                            deferredLoad = True
                            localPayload = cls.createLocalEpub(
                                item,
                                link,
                                instance.id
                            )
                            instance.epubsToLoad.append(localPayload)
                            break
                except TypeError as err:
                    logger.warning('Found link {} with no url {}'.format(
                        link,
                        url
                    ))
                    logger.debug(err)
            else:
                item['links'].append(link)
        
        if not deferredLoad: return cls.updateOrInsert(session, item)
        return None

    @classmethod
    def createLocalEpub(cls, item, link, instanceID):
        """Pass new item to epub storage pipeline. Does not store item record
        at this time, but defers until epub has been processed.
        The payload object takes several parameters:
        url: The URL of the ebook to be accessed
        id: The ID of the parent row of the item to be stored
        updated: Date the ebook was last updated at the source
        data: A raw block of the metadata associated with this item"""
        putItem = deepcopy(item)
        putItem['links'] = [link]
        epubPayload = {
            'url': link['url'],
            'id': instanceID,
            'updated': item['modified'],
            'data': putItem
        }

        for measure in item['measurements']:
            if measure['quantity'] == 'bytes':
                epubPayload['size'] = measure['value']
                break
        return epubPayload

    @classmethod
    def updateOrInsert(cls, session, itemData):
        """Will query for existing items and either update or insert an item
        record pending the outcome of that query"""
        
        existingID = Item.lookup(session, itemData['identifiers'])

        if existingID is not None:
            logger.debug('Found existing item by identifier')
            existing = session.query(Item).get(existingID)
            existing.update(session, itemData)
            outItem = existing
        else:
            logger.debug('Inserting new item record')
            outItem = Item.createItem(session, itemData)
        
        return outItem

    @classmethod
    def createItem(cls, session, itemData):
        item = Item(session=session)
        item.createTmpRelations(itemData)
        item.insertData(itemData)
        item.removeTmpRelations()
        delattr(item, 'session')
        return item

    @classmethod
    def lookup(self, session, identifiers, primaryID=None):
        if primaryID:
            item = Identifier.getByIdentifier(Item, session, [primaryID])
            if item: return item

        return Identifier.getByIdentifier(Item, session, identifiers)
    
    def insertData(self, itemData):
        """Insert a new item record"""
        for key, value in itemData.items(): setattr(self, key, value)

        self.addIdentifiers()
        self.addLinks()
        self.addMeasurements()
        self.addDates()
        self.addRights()
        self.addAgents()

        logger.info('Inserted item {}'.format(self))

    def update(self, session, itemData):
        """Update an existing item record"""

        self.session = session
        self.createTmpRelations(itemData)

        for field, value in itemData.items():
            if(value is not None and value.strip() != ''):
                setattr(self, field, value)

        self.updateIdentifiers()
        self.updateMeasurements()
        self.updateLinks()
        self.updateDates()
        self.updateRights()
        self.updateAgents()

        self.removeTmpRelations()
        delattr(self, 'session')

    def addIdentifiers(self):
        self.identifiers = {
            Identifier.returnOrInsert(self.session, i) 
            for i in self.tmp_identifiers
        }

    def updateIdentifiers(self):
        for identifier in self.tmp_identifiers:
            self.updateIdentifier(identifier)
    
    def updateIdentifier(self, identifier):
        try:
            self.identifiers.add(
                Identifier.returnOrInsert(self.session, identifier)
            )
        except DataError as err:
            logger.warning('Received invalid identifier')
            logger.debug(err)
    
    def addMeasurements(self):
        self.measurements = { 
            Measurement.insert(m) for m in self.tmp_measurements
        }

    def updateMeasurements(self):
        for measurement in self.tmp_measurements:
            self.measurements.add(
                Measurement.updateOrInsert(
                    self.session,
                    measurement,
                    Item,
                    self.id
                )
            )
    
    def addLinks(self):
        self.links = { Link(**l) for l in self.tmp_links }

    def updateLinks(self):
        for link in self.tmp_links:
            self.links.add(
                Link.updateOrInsert(self.session, link, Item, self.id)
            )
    
    def addDates(self):
        self.dates = { DateField.insert(d) for d in self.tmp_dates }

    def updateDates(self):
        for date in self.tmp_dates:
            self.dates.add(
                DateField.updateOrInsert(self.session, date, Item, self.id)
            )
    
    def addRights(self):
        self.rights = { 
            Rights.insert(r, dates=r.pop('dates', [])) for r in self.tmp_rights
        }

    def updateRights(self):
        for rightsStmt in self.tmp_rights:
            self.rights.add(
                Rights.updateOrInsert(
                    self.session,
                    rightsStmt,
                    Item,
                    self.id
                )
            )
    
    def addAgents(self):
        for agent in self.tmp_agents: self.addAgent(agent)
    
    def addAgent(self, agent):
        try:
            agentRec, roles = Agent.updateOrInsert(self.session, agent)
            for role in roles: AgentItems(agent=agentRec, item=self, role=role)
        except DataError:
            logger.warning('Unable to read agent {}'.format(agent['name']))

    def updateAgents(self):
        for agent in self.tmp_agents: self.updateAgent(agent)
    
    def updateAgent(self, agent):
        try:
            agentRec, roles = Agent.updateOrInsert(self.session, agent)
            if roles is None:
                roles = ['repository']
            for role in roles:
                if AgentItems.roleExists(self.session, agentRec, role, self.id) is None:
                    AgentItems(agent=agentRec, item=self, role=role)
        except DataError:
            logger.warning('Unable to read agent {}'.format(agent['name']))

    @classmethod
    def addReportData(cls, session, aceReport):
        """Adds accessibility report data to an item."""
        identifier = aceReport.pop('identifier', None)
        instanceID = aceReport.pop('instanceID', None)

        if identifier is not None:
            existingID = Identifier.getByIdentifier(cls, session, [identifier])

        if existingID is not None:
            existing = session.query(Item).get(existingID)
            newReport = Item.buildReport(aceReport)
            existing.access_reports.append(newReport)
    
    @classmethod
    def buildReport(cls, aceReport):
        violations = aceReport.pop('violations', [])
        aceReport['ace_version'] = aceReport.pop('aceVersion')
        aceReport['report_json'] = aceReport.pop('json')
        timestamp = aceReport.pop('timestamp', None)

        newReport = AccessReport(**aceReport)

        for violation, count in violations.items():
            newReport.measurements.append(Measurement(**{
                'quantity': violation,
                'value': count,
                'weight': 1,
                'taken_at': timestamp
            }))
        
        return newReport


class AccessReport(Core, Base):
    """Accessibility Reports are generated reports/scores of the
    accessbility of an epub file. These are used to provide general guidance
    on the readability of specific items"""
    __tablename__ = 'access_reports'
    id = Column(Integer, primary_key=True)
    ace_version = Column(String(25))
    score = Column(Float)
    report_json = Column(JSON, nullable=False)
    item_id = Column(Integer, ForeignKey('items.id'))

    item = relationship(
        'Item',
        back_populates='access_reports'
    )
    measurements = relationship(
        'Measurement',
        secondary=REPORT_MEASUREMENTS,
        back_populates='report'
    )

    def __repr__(self):
        return '<AccessReport(score={}, item={})>'.format(
            self.score,
            self.item
        )


class AgentItems(Core, Base):
    """Describes the relationship between an item and an agent, with the
    additional field of 'role' being added, allowing for multiple distinct
    relationships between an agent and an item. Identical to AgentInstances
    and AgentWorks"""
    __tablename__ = 'agent_items'
    item_id = Column(Integer, ForeignKey('items.id'), primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), primary_key=True, index=True)
    role = Column(String(64), primary_key=True)

    agentItemPkey = PrimaryKeyConstraint(
        'item_id', 'agent_id', 'role',
        name='agent_items_pkey'
    )

    item = relationship(
        Item,
        backref=backref('agent_items', cascade='all, delete-orphan')
    )
    agent = relationship('Agent')

    def __init__(self, item=None, agent=None, role=None):
        self.item = item
        self.agent = agent
        self.role = role

    @classmethod
    def roleExists(cls, session, agent, role, recordID):
        """Query database to check if a role exists between a specific work and
        agent"""
        return session.query(cls)\
            .filter(cls.agent_id == agent.id)\
            .filter(cls.item_id == recordID)\
            .filter(cls.role == role)\
            .one_or_none()
