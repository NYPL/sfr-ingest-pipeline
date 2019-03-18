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
    
    def __repr__(self):
        return '<Item(source={}, instance={})>'.format(
            self.source,
            self.instance
        )

    @classmethod
    def createOrStore(cls, session, item, instanceID):
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
                            cls.createLocalEpub(item, link, instanceID)
                            break
                except TypeError as err:
                    logger.warning('Found link {} with no url {}'.format(link, url))
                    logger.debug(err)
            else:
                item['links'].append(link)
        
        if len(item['links']) > 0:
            return cls.updateOrInsert(session, item)
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
    def updateOrInsert(cls, session, item):
        """Will query for existing items and either update or insert an item
        record pending the outcome of that query"""
        links = item.pop('links', [])
        identifiers = item.pop('identifiers', [])
        measurements = item.pop('measurements', [])
        dates = item.pop('dates', [])
        rights = item.pop('rights', [])
        agents = item.pop('agents', [])

        existingID = Identifier.getByIdentifier(cls, session, identifiers)

        if existingID is not None:
            logger.debug('Found existing item by identifier')
            existing = session.query(Item).get(existingID)
            cls.update(
                session,
                existing,
                item,
                identifiers=identifiers,
                links=links,
                measurements=measurements,
                dates=dates,
                rights=rights,
                agents=agents
            )
            return existing, 'updated'

        logger.debug('Inserting new item record')
        itemRec = cls.insert(
            session,
            item,
            links=links,
            measurements=measurements,
            identifiers=identifiers,
            dates=dates,
            rights=rights,
            agents=agents
        )

        return itemRec, 'inserted'

    @classmethod
    def insert(cls, session, itemData, **kwargs):
        """Insert a new item record"""
        item = cls(**itemData)

        links = kwargs.get('links', [])
        measurements = kwargs.get('measurements', [])
        identifiers = kwargs.get('identifiers', [])
        dates = kwargs.get('dates', [])
        rights = kwargs.get('rights', [])
        agents = kwargs.get('agents', [])

        for identifier in identifiers:
            try:
                item.identifiers.append(Identifier.insert(identifier))
            except DataError as err:
                logger.warning('Received invalid identifier')
                logger.debug(err)

        for link in links:
            newLink = Link(**link)
            item.links.append(newLink)

        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            item.measurements.append(measurementRec)

        for date in dates:
            newDate = DateField.insert(date)
            item.dates.append(newDate)
        
        for rightsStmt in rights:
            rightsDates = rightsStmt.pop('dates', [])
            newRights = Rights.insert(rightsStmt, dates=rightsDates)
            item.rights.append(newRights)

        for agent in agents:
            try:
                agentRec, roles = Agent.updateOrInsert(session, agent)
                for role in roles:
                    AgentItems(
                        agent=agentRec,
                        item=item,
                        role=role
                    )
            except DataError:
                logger.warning('Unable to read agent {}'.format(agent['name']))

        return item

    @classmethod
    def update(cls, session, existing, item, **kwargs):
        """Update an existing item record"""

        links = kwargs.get('links', [])
        measurements = kwargs.get('measurements', [])
        identifiers = kwargs.get('identifiers', [])
        dates = kwargs.get('dates', [])
        rights = kwargs.get('rights', [])
        agents = kwargs.get('agents', [])

        for field, value in item.items():
            if(value is not None and value.strip() != ''):
                setattr(existing, field, value)

        for identifier in identifiers:
            try:
                status, idenRec = Identifier.returnOrInsert(
                    session,
                    identifier,
                    existing.id
                )
                if status == 'new':
                    existing.identifiers.append(idenRec)
            except DataError as err:
                logger.warning('Received invalid identifier')
                logger.debug(err)

        for measurement in measurements:
            op, measurementRec = Measurement.updateOrInsert(
                session,
                measurement,
                Item,
                existing.id
            )
            if op == 'insert':
                existing.measurements.append(measurementRec)

        for link in links:
            existingLink = Link.lookupLink(session, link, cls, existing.id)
            if existingLink is None:
                existing.links.append(Link(**link))
            else:
                Link.update(existingLink, link)

        for date in dates:
            updateDate = DateField.updateOrInsert(session, date, Item, existing.id)
            if updateDate is not None:
                existing.dates.append(updateDate)
        
        for rightsStmt in rights:
            updateRights = Rights.updateOrInsert(
                session,
                rightsStmt,
                Item,
                existing.id
            )
            if updateRights is not None:
                existing.rights.append(updateRights)
        
        for agent in agents:
            try:
                agentRec, roles = Agent.updateOrInsert(session, agent)
                if roles is None:
                    roles = ['repository']
                for role in roles:
                    if AgentItems.roleExists(session, agentRec, role, Item, existing.id) is None:
                        AgentItems(
                            agent=agentRec,
                            item=existing,
                            role=role
                        )
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
    role = Column(String(64))

    agentItemPkey = PrimaryKeyConstraint('item_id', 'agent_id', 'role', name='agent_items_pkey')

    item = relationship(
        Item,
        backref=backref('agent_items', cascade='all, delete-orphan')
    )
    agent = relationship('Agent')

    @classmethod
    def roleExists(cls, session, agent, role, model, recordID):
        """Query database to check if a role exists between a specific work and
        agent"""
        return session.query(cls)\
            .join(Agent)\
            .join(model)\
            .filter(Agent.id == agent.id)\
            .filter(model.id == recordID)\
            .filter(cls.role == role)\
            .one_or_none()
