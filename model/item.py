import uuid
import os
from sqlalchemy import (
    Column,
    Date,
    Enum,
    ForeignKey,
    Index,
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
from model.measurement import ITEM_MEASUREMENTS, REPORT_MEASUREMENTS, Measurement
from model.identifiers import ITEM_IDENTIFIERS
from model.link import ITEM_LINKS, Link

from lib.outputManager import OutputManager

class Item(Core, Base):

    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    source = Column(Unicode, index=True)
    content_type = Column(Unicode, index=True)
    modified = Column(DateTime, index=True)
    drm = Column(Unicode, index=True)
    rights_uri = Column(Unicode, index=True)

    instance_id = Column(Integer, ForeignKey('instances.id'))

    instance = relationship('Instance', back_populates='items')
    measurements = relationship('Measurement', secondary=ITEM_MEASUREMENTS, back_populates='item')
    identifiers = relationship('Identifier', secondary=ITEM_IDENTIFIERS, back_populates='item')
    agents = association_proxy('agent_items', 'agents')
    access_reports = relationship('AccessReport', back_populates='item')
    links = relationship('Link', secondary=ITEM_LINKS, back_populates='items')

    def __repr__(self):
        return '<Item(source={}, instance={})>'.format(self.source, self.instance)


    @classmethod
    def createLocalEpub(cls, item, instanceID):
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

        link = item.pop('link', None)
        measurements = item.pop('measurements', [])

        itemRec = Item.insert(
            item,
            link=link,
            measurements=measurements
        )

        return itemRec


    @classmethod
    def insert(cls, itemData, **kwargs):

        item = Item(**itemData)

        link = kwargs.get('link', None)
        measurements = kwargs.get('measurements', [])

        if link is not None:
            newLink = Link(**link)
            item.links.append(newLink)

        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            item.measurements.append(measurementRec)

        return item


class AccessReport(Core, Base):

    __tablename__ = 'access_reports'
    id = Column(Integer, primary_key=True)
    ace_version = Column(String(25))
    score = Column(Float, index=True)
    report_json = Column(JSON, nullable=False)
    item_id = Column(Integer, ForeignKey('items.id'))

    item = relationship('Item', back_populates='access_reports')
    measurements = relationship('Measurement', secondary=REPORT_MEASUREMENTS, back_populates='report')

    def __repr__(self):
        return '<AccessReport(score={}, item={})>'.format(self.score, self.item)


class AgentItems(Core, Base):

    __tablename__ = 'agent_items'
    item_id = Column(Integer, ForeignKey('items.id'), primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), primary_key=True)
    role = Column(String(64))

    item = relationship(Item, backref=backref('agent_items', cascade='all, delete-orphan'))
    agent = relationship('Agent')
