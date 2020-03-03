import re

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Unicode,
    Table
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import JSON

from .core import Base, Core

WORK_LINKS = Table(
    'work_links',
    Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id'), index=True),
    Column('link_id', Integer, ForeignKey('links.id'), index=True)
)

INSTANCE_LINKS = Table(
    'instance_links',
    Base.metadata,
    Column('instance_id', Integer, ForeignKey('instances.id'), index=True),
    Column('link_id', Integer, ForeignKey('links.id'), index=True)
)

ITEM_LINKS = Table(
    'item_links',
    Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id'), index=True),
    Column('link_id', Integer, ForeignKey('links.id'), index=True)
)

AGENT_LINKS = Table(
    'agent_links',
    Base.metadata,
    Column('agent_id', Integer, ForeignKey('agents.id'), index=True),
    Column('link_id', Integer, ForeignKey('links.id'), index=True)
)


class Link(Core, Base):
    """A generic class for describing a reference to an external resource"""
    __tablename__ = 'links'
    id = Column(Integer, primary_key=True)
    url = Column(Unicode, index=True)
    media_type = Column(String(50))
    content = Column(Unicode)
    flags = Column(JSON)
    md5 = Column(Unicode)

    thumbnail = Column(Integer, ForeignKey('links.id'))

    works = relationship(
        'Work',
        secondary=WORK_LINKS,
        back_populates='links'
    )
    instances = relationship(
        'Instance',
        secondary=INSTANCE_LINKS,
        back_populates='links'
    )
    items = relationship(
        'Item',
        secondary=ITEM_LINKS,
        back_populates='links'
    )
    agents = relationship(
        'Agent',
        secondary=AGENT_LINKS,
        back_populates='links'
    )

    @validates('url')
    def removeHTTP(self, key, url):
        """Ensures that http:// and https:// are removed from all URLs to ensure
        equality are valid

        Arguments:
            key {str} -- Field being validated
            name {str} -- The sort_name value for the current record

        Returns:
            str -- The clean version of the URL
        """
        return Link.httpRegexSub(url)

    def __repr__(self):
        return '<Link(url={}, media_type={})>'.format(
            self.url,
            self.media_type
        )

    @classmethod
    def updateOrInsert(cls, session, link, model, recordID):
        """Query the database for a link on the current record. If found,
        update the existing link, if not, insert new row"""
        outLink = Link.lookupLink(session, link, model, recordID)
        if outLink is None: outLink = Link(**link)
        else: outLink.update(link)
        
        return outLink

    def update(self, linkData):
        """Update fields on existing link"""
        for field, value in linkData.items():
            if field == 'flags':
                setattr(self, field, value)
            elif(value is not None and value.strip() != ''):
                setattr(self, field, value)

    @classmethod
    def lookupLink(cls, session, link, model, recordID):
        """Query database for link related to current record. Return link
        if found, otherwise return None"""
        checkURL = Link.httpRegexSub(link.get('url', None))
        return session.query(cls)\
            .join(model.__tablename__)\
            .filter(model.id == recordID)\
            .filter(cls.url == checkURL)\
            .one_or_none()

    @staticmethod
    def httpRegexSub(url):
        if isinstance(url, str):
            return re.sub(r'^http(?:s)?:\/\/', '', url.lower())
        else:
            return url
