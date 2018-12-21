import uuid
from sqlalchemy import (
    Column,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Unicode,
    DateTime,
    Table
)
from sqlalchemy.orm import relationship

from model.core import Base, Core

WORK_IDENTIFIERS = Table('work_identifiers', Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id')),
    Column('identifier_id', Integer, ForeignKey('identifiers.id'))
)

INSTANCE_IDENTIFIERS = Table('instance_identifiers', Base.metadata,
    Column('instance_id', Integer, ForeignKey('instances.id')),
    Column('identifier_id', Integer, ForeignKey('identifiers.id'))
)

ITEM_IDENTIFIERS = Table('item_identifiers', Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id')),
    Column('identifier_id', Integer, ForeignKey('identifiers.id'))
)

class Gutenberg(Core, Base):

    __tablename__ = 'gutenberg'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='gutenberg')

    def __repr__(self):
        return '<Gutenberg(value={})>'.format(self.value)


class OCLC(Core, Base):

    __tablename__ = 'oclc'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='oclc')

    def __repr__(self):
        return '<OCLC(value={})>'.format(self.value)


class LCCN(Core, Base):

    __tablename__ = 'lccn'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='lccn')

    def __repr__(self):
        return '<LCCN(value={})>'.format(self.value)


class ISBN(Core, Base):

    __tablename__ = 'isbn'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='isbn')

    def __repr__(self):
        return '<ISBN(value={})>'.format(self.value)


class OWI(Core, Base):

    __tablename__ = 'owi'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='owi')

    def __repr__(self):
        return '<OWI(value={})>'.format(self.value)


class ISSN(Core, Base):

    __tablename__ = 'issn'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='issn')

    def __repr__(self):
        return '<ISSN(value={})>'.format(self.value)


class Identifier(Base):

    __tablename__ = 'identifiers'
    id = Column(Integer, primary_key=True)
    type = Column(Unicode, index=True)

    work = relationship('Work', secondary=WORK_IDENTIFIERS, back_populates='identifiers')
    instance = relationship('Instance', secondary=INSTANCE_IDENTIFIERS, back_populates='identifiers')
    item = relationship('Item', secondary=ITEM_IDENTIFIERS, back_populates='identifiers')

    # Related tables for specific identifier types
    gutenberg = relationship('Gutenberg', back_populates='identifier')
    oclc = relationship('OCLC', back_populates='identifier')
    lccn = relationship('LCCN', back_populates='identifier')
    isbn = relationship('ISBN', back_populates='identifier')
    issn = relationship('ISSN', back_populates='identifier')
    owi = relationship('OWI', back_populates='identifier')

    identifierTypes = {
        'gutenberg': Gutenberg,
        'oclc': OCLC,
        'owi': OWI,
        'lccn': LCCN,
        'isbn': ISBN,
        'issn': ISSN
    }



    def __repr__(self):
        return '<Identifier(type={})>'.format(self.type)

    @classmethod
    def returnOrInsert(cls, session, identifier, model, recordID):

        existingIden = Identifier.lookupIdentifier(session, identifier, model, recordID)
        if existingIden is not None:
            return 'existing', existingIden

        return 'new', Identifier.insert(identifier)


    @classmethod
    def insert(cls, identifier):
        coreIden = Identifier(type=identifier['type'])
        specificIden = cls.identifierTypes[identifier['type']]
        idenRec = specificIden(value=identifier['identifier'])
        idenField = getattr(coreIden, identifier['type'])
        idenField.append(idenRec)
        return coreIden


    @classmethod
    def lookupIdentifier(cls, session, identifier, model, recordID):
        idenType = identifier['type']
        existing = session.query(model) \
            .join("identifiers", idenType) \
            .filter(cls.identifierTypes[idenType].value == identifier['identifier']) \
            .filter(model.id == recordID) \
            .all()

        if len(existing) == 1:
            return existing[0]
        elif len(existing) > 1:
            print("Found multiple identifiers for this!")
            raise
        else:
            return None

    @classmethod
    def getByIdentifier(cls, model, session, identifiers):
        for ident in identifiers:
            idenType = ident['type']
            existing = session.query(model)\
                .join("identifiers", idenType)\
                .filter(cls.identifierTypes[idenType].value == ident['identifier'])\
                .all()

            if len(existing) == 1:
                return existing[0]
            elif len(existing) > 1:
                print("Found multiple references!")
                raise
        else:
            return None
