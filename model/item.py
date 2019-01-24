import os
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

from lib.outputManager import OutputManager
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
    rights_uri = Column(Unicode, index=True)

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
    dates = relationship(
        'DateField',
        secondary=ITEM_DATES,
        back_populates='items'
    )

    def __repr__(self):
        return '<Item(source={}, instance={})>'.format(
            self.source,
            self.instance
        )

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
    def createLocalEpub(cls, item, instanceID):
        """Pass new item to epub storage pipeline. Does not store item record
        at this time, but defers until epub has been processed.

        The payload object takes several parameters:
        url: The URL of the ebook to be accessed
        id: The ID of the parent row of the item to be stored
        updated: Date the ebook was last updated at the source
        data: A raw block of the metadata associated with this item"""

        url = item['link']['url']

        epubPayload = {
            'url': item['link']['url'],
            'id': instanceID,
            'updated': item['modified'],
            'data': item
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
        link = item.pop('link', None)
        identifier = item.pop('identifier', None)
        measurements = item.pop('measurements', [])
        dates = item.pop('dates', [])

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
                dates=dates
            )
            return existing, 'updated'

        logger.debug('Inserting new item record')
        itemRec = cls.insert(
            session,
            item,
            link=link,
            measurements=measurements,
            identifier=identifier,
            dates=dates
        )

        return itemRec, 'inserted'

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
            item.dates.append(newDate)

        return item

    @classmethod
    def update(cls, session, existing, item, **kwargs):
        """Update an existing item record"""

        link = kwargs.get('link', None)
        measurements = kwargs.get('measurements', [])
        identifier = kwargs.get('identifier', None)
        dates = kwargs.get('dates', [])

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

        if type(link) is dict:
            existingLink = Link.lookupLink(session, link, cls, existing.id)
            if existingLink is None:
                existing.links.append(Link(**link))
            else:
                Link.update(existingLink, link)
        elif type(link) is list:
            for linkItem in link:
                existingLink = Link.lookupLink(session, linkItem, cls, existing.id)
                if existingLink is None:
                    existing.links.append(Link(**linkItem))
                else:
                    Link.update(existingLink, link)

        for date in dates:
            updateDate = DateField.updateOrInsert(session, date, Item, existing.id)
            if updateDate is not None:
                existing.dates.append(updateDate)

    @classmethod
    def addReportData(cls, session, reportData):
        """Adds accessibility report data to an item."""
        identifier = reportData.pop('identifier', None)

        existing = None
        if identifier is not None:
            existing = Identifier.getByIdentifier(cls, session, [identifier])
            return None

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

    item = relationship(
        Item,
        backref=backref('agent_items', cascade='all, delete-orphan')
    )
    agent = relationship('Agent')
