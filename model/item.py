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

from model.core import Base, Core
from model.measurement import (
    ITEM_MEASUREMENTS,
    REPORT_MEASUREMENTS,
    Measurement
)
from model.identifiers import ITEM_IDENTIFIERS, Identifier
from model.link import ITEM_LINKS, Link
from model.date import ITEM_DATES, DateField
from model.rights import Rights, ITEM_RIGHTS
from model.agent import Agent

from lib.outputManager import OutputManager
from helpers.logHelpers import createLog
from helpers.errorHelpers import DataError

logger = createLog('items')

# SOURCES
# gut = GUTENBERG
# ia  = INTERNET ARCHIVE
SOURCE_REGEX = {
    'gut': r'gutenberg.org\/ebooks\/[0-9]+\.epub\.(?:no|)images$',
    'ia': r'archive.org\/details\/[a-z0-9]+$'
}

EPUB_SOURCES = ['gut']

class Item(Core, Base):
    """An item is an individual copy of a work in the FRBR model. In the
    digital realm this refers to a specifically stored copy of the work"""
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    source = Column(Unicode, index=True)
    content_type = Column(Unicode, index=True)
    modified = Column(DateTime, index=True)
    drm = Column(Unicode, index=True)
    
    instance_id = Column(Integer, ForeignKey('instances.id'))

    instance = relationship(
        'Instance',
        back_populates='items'
    )
    measurements = relationship(
        'Measurement',
        secondary=ITEM_MEASUREMENTS,
        back_populates='item'
    )
    identifiers = relationship(
        'Identifier',
        secondary=ITEM_IDENTIFIERS,
        back_populates='item'
    )
    agents = association_proxy(
        'agent_items',
        'agents'
    )
    access_reports = relationship(
        'AccessReport',
        back_populates='item'
    )
    links = relationship(
        'Link',
        secondary=ITEM_LINKS,
        back_populates='items'
    )

    CHILD_FIELDS = [
        'links',
        'identifiers',
        'measurements',
        'dates',
        'rights',
        'agents'
    ]

    def __repr__(self):
        return '<Item(source={}, instance={})>'.format(
            self.source,
            self.instance
        )

    @classmethod
    def _buildChildDict(cls, itemData):
        return { field: itemData.pop(field, []) for field in cls.CHILD_FIELDS }

    @classmethod
    def createOrStore(cls, session, item, instance):
        links = deque(item.pop('links', []))
        item['links'] = []
        while len(links) > 0:
            link = links.popleft()
            url = link['url']
            if not isinstance(url, (str,)):
                continue
            for source, regex in SOURCE_REGEX.items():
                try:
                    if re.search(regex, url):
                        if source in EPUB_SOURCES:

                            # We need to get the ID of the instance to allow 
                            # for asynchronously storing the ePub file, so
                            # instance is added and flushed here
                            if instance.id is None:
                                session.add(instance)
                                session.flush()

                            cls.createLocalEpub(item, link, instance.id)
                            break
                except TypeError as err:
                    logger.warning('Found link {} with no url {}'.format(
                        link,
                        url
                    ))
                    logger.debug(err)
            else:
                item['links'].append(link)
        
        if len(item['links']) > 0:
            return cls.insert(session, item)
        else:
            return None, 'creating'

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

        OutputManager.putKinesis(epubPayload, os.environ['EPUB_STREAM'])

    @classmethod
    def insert(cls, session, itemData):
        """Insert a new item record"""

        childFields = Item._buildChildDict(itemData)

        item = cls(**itemData)

        Item._addIdentifiers(session, item, childFields['identifiers'])

        Item._addAgents(session, item, childFields['agents'])

        Item._addMeasurements(session, item, childFields['measurements'])

        Item._addLinks(item, childFields['links'])

        Item._addDates(item, childFields['dates'])

        Item._addRights(item, childFields['rights'])

        return item, 'inserted'

    @classmethod
    def _addIdentifiers(cls, session, item, identifiers):
        for iden in identifiers:
            try:
                status, idenRec = Identifier.returnOrInsert(
                    session,
                    iden
                )
                item.identifiers.append(idenRec)
            except DataError as err:
                logger.warning('Received invalid identifier')
                logger.debug(err)
    
    @classmethod
    def _addAgents(cls, session, item, agents):
        relsCreated = []
        for agent in agents:
            try:
                agentRec, roles = Agent.updateOrInsert(session, agent)
                for role in roles:
                    if (agentRec.name, role) in relsCreated: continue
                    relsCreated.append((agentRec.name, role))
                    AgentItems(
                        agent=agentRec,
                        item=item,
                        role=role
                    )
            except DataError:
                logger.warning('Unable to read agent {}'.format(agent['name']))
    
    @classmethod
    def _addMeasurements(cls, session, item, measurements):
        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            item.measurements.append(measurementRec)
    
    @classmethod
    def _addLinks(cls, item, links):
        for link in links:
            newLink = Link(**link)
            item.links.append(newLink)
    
    @classmethod
    def _addDates(cls, item, dates):
        for date in dates:
            newDate = DateField.insert(date)
            item.dates.append(newDate)
    
    @classmethod
    def _addRights(cls, item, rights):
        for rightsStmt in rights:
            rightsDates = rightsStmt.pop('dates', [])
            newRights = Rights.insert(rightsStmt, dates=rightsDates)
            item.rights.append(newRights)

    @classmethod
    def addReportData(cls, session, aceReport):
        """Adds accessibility report data to an item."""
        identifier = aceReport.pop('identifier', None)
        instanceID = aceReport.pop('instanceID', None)

        if identifier is not None:
            existingID = Identifier.getByIdentifier(cls, session, [identifier])

        if existingID is not None:
            existing = session.query(Item).get(existingID)
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

            existing.access_reports.append(newReport)
            return existing


class AccessReport(Core, Base):
    """Accessibility Reports are generated reports/scores of the
    accessbility of an epub file. These are used to provide general guidance
    on the readability of specific items"""
    __tablename__ = 'access_reports'
    id = Column(Integer, primary_key=True)
    ace_version = Column(String(25))
    score = Column(Float, index=True)
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
    item_id = Column(Integer, ForeignKey('items.id'), primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), primary_key=True)
    role = Column(String(64), primary_key=True)

    agentItemPkey = PrimaryKeyConstraint('item_id', 'agent_id', 'role', name='agent_items_pkey')

    item = relationship(
        Item,
        backref=backref('agent_items', cascade='all, delete-orphan')
    )
    agent = relationship('Agent')

    @classmethod
    def roleExists(cls, session, agent, role, recordID):
        """Query database to check if a role exists between a specific work and
        agent"""
        return session.query(cls)\
            .filter(cls.agent_id == agent.id)\
            .filter(cls.item_id == recordID)\
            .filter(cls.role == role)\
            .one_or_none()
