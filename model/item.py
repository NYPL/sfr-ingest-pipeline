import re
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Float,
    String,
    Unicode,
    DateTime,
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
from model.rights import Rights

from helpers.logHelpers import createLog

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
    agents = relationship(
        'AgentItems',
        back_populates='item'
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
    
    def __dir__(self):
        return ['source', 'content_type', 'modified', 'drm']

    @classmethod
    def createOrStore(cls, session, item, instanceID):

        url = item['link']['url']

        for source, regex in SOURCE_REGEX.items():
            if re.search(regex, url):
                if source in EPUB_SOURCES:
                    cls.createLocalEpub(item, instanceID)
                    return None
        else:
            return cls.updateOrInsert(session, item)

    @classmethod
    def updateOrInsert(cls, session, item):
        """Will query for existing items and either update or insert an item
        record pending the outcome of that query"""
        link = item.pop('link', None)
        identifier = item.pop('identifier', None)
        measurements = item.pop('measurements', [])
        dates = item.pop('dates', [])
        rights = item.pop('rights', [])

        existing = None
        if identifier is not None:
            existing = Identifier.getByIdentifier(cls, session, [identifier])

        if existing is not None:
            logger.debug('Found existing item by identifier')
            cls.update(
                session,
                existing,
                item,
                identifier=identifier,
                link=link,
                measurements=measurements,
                dates=dates,
                rights=rights
            )
            return None

        logger.debug('Inserting new item record')
        itemRec = cls.insert(
            session,
            item,
            link=link,
            measurements=measurements,
            identifier=identifier,
            dates=dates,
            rights=rights
        )

        return itemRec

    @classmethod
    def insert(cls, session, itemData, **kwargs):
        """Insert a new item record"""
        item = cls(**itemData)

        link = kwargs.get('link', None)
        measurements = kwargs.get('measurements', [])
        identifier = kwargs.get('identifier', None)
        dates = kwargs.get('dates', [])

        item.identifiers.append(Identifier.insert(identifier))

        if link is not None:
            newLink = Link(**link)
            item.links.append(newLink)

        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            item.measurements.append(measurementRec)

        for date in dates:
            newDate = DateField.insert(date)
            work.dates.append(newDate)
        
        for rightsStmt in rights:
            newRights = Rights.insert(rightsStmt)
            item.rights.append(newRights)

        return item

    @classmethod
    def update(cls, session, existing, item, **kwargs):
        """Update an existing item record"""

        link = kwargs.get('link', None)
        measurements = kwargs.get('measurements', [])
        identifier = kwargs.get('identifier', None)
        dates = kwawrgs.get('dates', [])
        rights = kwargs.get('rights', [])

        for field, value in item.items():
            if(value is not None and value.strip() != ''):
                setattr(existing, field, value)

        status, idenRec = Identifier.returnOrInsert(
            session,
            identifier,
            cls,
            existing.id
        )

        if status == 'new':
            existing.identifiers.append(idenRec)

        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            existing.measurements.append(measurementRec)

        if link is not None:
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

    @classmethod
    def addReportData(cls, session, reportData):
        """Adds accessibility report data to an item."""
        identifier = reportData.pop('identifier', None)

        existing = None
        if identifier is not None:
            existing = Identifier.getByIdentifier(cls, session, [identifier])

        if existing is not None:
            aceReport = reportData['data']

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
    
    def __dir__(self):
        return ['ace_version', 'score']


class AgentItems(Core, Base):
    """Describes the relationship between an item and an agent, with the
    additional field of 'role' being added, allowing for multiple distinct
    relationships between an agent and an item. Identical to AgentInstances
    and AgentWorks"""
    __tablename__ = 'agent_items'
    item_id = Column(Integer, ForeignKey('items.id'), primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), primary_key=True)
    role = Column(String(64))

    item = relationship(
        Item,
        backref=backref('agent_items', cascade='all, delete-orphan')
    )
    agent = relationship('Agent')
