from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Unicode,
    Table
)
from sqlalchemy.orm import relationship

from helpers.logHelpers import createLog
from helpers.errorHelpers import DBError

from model.core import Base, Core

logger = createLog('identifiers')

WORK_IDENTIFIERS = Table(
    'work_identifiers',
    Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id')),
    Column('identifier_id', Integer, ForeignKey('identifiers.id'))
)

INSTANCE_IDENTIFIERS = Table(
    'instance_identifiers',
    Base.metadata,
    Column('instance_id', Integer, ForeignKey('instances.id')),
    Column('identifier_id', Integer, ForeignKey('identifiers.id'))
)

ITEM_IDENTIFIERS = Table(
    'item_identifiers',
    Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id')),
    Column('identifier_id', Integer, ForeignKey('identifiers.id'))
)


class Gutenberg(Core, Base):
    """Table for Gutenberg Identifiers"""
    __tablename__ = 'gutenberg'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='gutenberg')

    def __repr__(self):
        return '<Gutenberg(value={})>'.format(self.value)


class OCLC(Core, Base):
    """Table for OCLC Identifiers"""
    __tablename__ = 'oclc'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='oclc')

    def __repr__(self):
        return '<OCLC(value={})>'.format(self.value)


class LCCN(Core, Base):
    """Table for Library of Congress Control Numbers"""
    __tablename__ = 'lccn'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='lccn')

    def __repr__(self):
        return '<LCCN(value={})>'.format(self.value)


class ISBN(Core, Base):
    """Table for ISBNs (10 and 13 digits)"""
    __tablename__ = 'isbn'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='isbn')

    def __repr__(self):
        return '<ISBN(value={})>'.format(self.value)


class OWI(Core, Base):
    """Table for OCLC Work Identifiers"""
    __tablename__ = 'owi'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='owi')

    def __repr__(self):
        return '<OWI(value={})>'.format(self.value)


class ISSN(Core, Base):
    """Table for ISSNs"""
    __tablename__ = 'issn'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='issn')

    def __repr__(self):
        return '<ISSN(value={})>'.format(self.value)


class LCC(Core, Base):
    """Table for Library of Congress Cataloging Numbers"""
    __tablename__ = 'lcc'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='lcc')

    def __repr__(self):
        return '<LCC(value={})>'.format(self.value)


class DDC(Core, Base):
    """Table for Dewey Decimal Control Numbers"""
    __tablename__ = 'ddc'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='ddc')

    def __repr__(self):
        return '<DDC(value={})>'.format(self.value)


class GENERIC(Core, Base):
    """Table for generic or otherwise uncontroller identifiers"""
    __tablename__ = 'generic'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='generic')

    def __repr__(self):
        return '<GENERIC(value={})>'.format(self.value)


class Identifier(Base):
    """Core table for Identifiers. This relates specific identifiers, each
    contained within their own table, to FRBR entities. This structure allows
    for independent validation of different identifier types while maintaining
    a simple relationship model between identifiers and the FRBR entities."""
    __tablename__ = 'identifiers'
    id = Column(Integer, primary_key=True)
    type = Column(Unicode, index=True)

    work = relationship(
        'Work',
        secondary=WORK_IDENTIFIERS,
        back_populates='identifiers'
    )
    instance = relationship(
        'Instance',
        secondary=INSTANCE_IDENTIFIERS,
        back_populates='identifiers'
    )
    item = relationship(
        'Item',
        secondary=ITEM_IDENTIFIERS,
        back_populates='identifiers'
    )

    # Related tables for specific identifier types
    gutenberg = relationship('Gutenberg', back_populates='identifier')
    oclc = relationship('OCLC', back_populates='identifier')
    lccn = relationship('LCCN', back_populates='identifier')
    isbn = relationship('ISBN', back_populates='identifier')
    issn = relationship('ISSN', back_populates='identifier')
    owi = relationship('OWI', back_populates='identifier')
    lcc = relationship('LCC', back_populates='identifier')
    ddc = relationship('DDC', back_populates='identifier')
    generic = relationship('GENERIC', back_populates='identifier')

    identifierTypes = {
        'gutenberg': Gutenberg,
        'oclc': OCLC,
        'owi': OWI,
        'lccn': LCCN,
        'isbn': ISBN,
        'issn': ISSN,
        'lcc': LCC,
        'ddc': DDC,
        None: GENERIC
    }

    def __repr__(self):
        return '<Identifier(type={})>'.format(self.type)

