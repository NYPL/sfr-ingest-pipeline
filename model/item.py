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

from helpers.logHelpers import createLog
from helpers.errorHelpers import DataError

logger = createLog('items')


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
        back_populates='item',
        collection_class=set
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
    def updateOrInsert(cls, session, item):
        """Will query for existing items and either update or insert an item
        record pending the outcome of that query"""
        
        existingID = Identifier.getByIdentifier(
            cls,
            session,
            item['identifiers']
        )

        if existingID is not None:
            logger.debug('Found existing item by identifier')
            existing = session.query(Item).get(existingID)
            cls.update(session, existing, item)
            return existing, 'updated'

        logger.debug('Inserting new item record')
        itemRec = cls.insert(session, item)

        return itemRec, 'inserted'

    @classmethod
    def insert(cls, session, itemData):
        """Insert a new item record"""

        childFields = Item._buildChildDict(itemData)

        item = cls(**itemData)

        item.identifiers = {
            Identifier.returnOrInsert(session, i) 
            for i in childFields['identifiers']
        }
        
        item.links = [ Link(**l) for l in childFields['links'] ]

        item.measurements = [ 
            Measurement.insert(m) 
            for m in childFields['measurements']
        ]

        item.dates = [ DateField.insert(d) for d in childFields['dates'] ]
        
        item.rights = [ 
            Rights.insert(r, dates=r.pop('dates', [])) 
            for r in childFields['rights']
        ]

        for agent in childFields['agents']:
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
    def update(cls, session, existing, item):
        """Update an existing item record"""

        childFields = Item._buildChildDict(item)

        for field, value in item.items():
            if(value is not None and value.strip() != ''):
                setattr(existing, field, value)

        for identifier in childFields['identifiers']:
            try:
                existing.identifiers.add(
                    Identifier.returnOrInsert(session, identifier)
                )
            except DataError as err:
                logger.warning('Received invalid identifier')
                logger.debug(err)

        for measurement in childFields['measurements']:
            op, measurementRec = Measurement.updateOrInsert(
                session,
                measurement,
                Item,
                existing.id
            )
            if op == 'insert':
                existing.measurements.append(measurementRec)

        for link in childFields['links']:
            existingLink = Link.lookupLink(session, link, cls, existing.id)
            if existingLink is None:
                existing.links.append(Link(**link))
            else:
                Link.update(existingLink, link)

        for date in childFields['dates']:
            updateDate = DateField.updateOrInsert(session, date, Item, existing.id)
            if updateDate is not None:
                existing.dates.append(updateDate)
        
        for rightsStmt in childFields['rights']:
            updateRights = Rights.updateOrInsert(
                session,
                rightsStmt,
                Item,
                existing.id
            )
            if updateRights is not None:
                existing.rights.append(updateRights)
        
        for agent in childFields['agents']:
            try:
                agentRec, roles = Agent.updateOrInsert(session, agent)
                if roles is None:
                    roles = ['repository']
                for role in roles:
                    if AgentItems.roleExists(session, agentRec, role, existing.id) is None:
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
