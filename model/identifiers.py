from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Unicode,
    Table
)
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

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


class Hathi(Core, Base):
    """Table for HathiTrust Identifiers"""
    __tablename__ = 'hathi'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True)

    identifier_id = Column(Integer, ForeignKey('identifiers.id'))

    identifier = relationship('Identifier', back_populates='hathi')

    def __repr__(self):
        return '<Hathi(value={})>'.format(self.value)


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
    hathi = relationship('Hathi', back_populates='identifier')
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
        'hathi': Hathi,
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

    @classmethod
    def returnOrInsert(cls, session, identifier, model, recordID):
        """Manages either the creation or return of an existing identifier"""

        if identifier is None:
            return None, None
        existingIdenID = Identifier.lookupIdentifier(
            session,
            identifier,
            model,
            recordID
        )
        if existingIdenID is not None:
            return 'existing', session.query(model).get(existingIdenID)

        return 'new', Identifier.insert(identifier)

    @classmethod
    def insert(cls, identifier):
        """Inserts a new identifier"""

        # Create a new entry in the core Identifier table
        coreIden = Identifier(type=identifier['type'])

        # Load the model for the identifier type being stored
        specificIden = cls.identifierTypes[identifier['type']]

        # Create new entry in that specific identifiers table
        idenRec = specificIden(value=identifier['identifier'])

        # Add new identifier entry to the core table record
        idenTable = identifier['type'] if identifier['type'] is not None else 'generic'
        idenField = getattr(coreIden, idenTable)
        idenField.append(idenRec)

        return coreIden

    @classmethod
    def lookupIdentifier(cls, session, identifier, model, recordID):
        """Query database for a specific identifier. Return if found and
        raise an error if duplicate identifiers are found for a single
        type."""
        idenType = identifier['type']
        idenTable = idenType if idenType is not None else 'generic'
        
        try:
            return session.query(model.id) \
                .join('identifiers', idenTable) \
                .filter(cls.identifierTypes[idenType].value == identifier['identifier']) \
                .filter(model.id == recordID) \
                .one()
        
        except MultipleResultsFound:
            logger.error('Found multiple identifiers for {} ({})'.format(
                identifier['identifier'],
                identifier['type']
            ))
            raise DBError(identifier['type'], 'Found duplicate identifiers')
        except NoResultFound:
            pass

        return None

    @classmethod
    def getByIdentifier(cls, model, session, identifiers):
        """Query database for a record related to a specific identifier. Return
        if found and raise an error if multiple matching records are found."""
        for ident in identifiers:
            logger.debug('Querying database for identifier {} ({})'.format(
                ident['identifier'],
                ident['type']
            ))
            idenType = ident['type']
            idenTable = idenType if idenType is not None else 'generic'
            
            try:
                return session.query(model.id)\
                    .join('identifiers', idenTable)\
                    .filter(cls.identifierTypes[idenType].value == ident['identifier'])\
                    .one()
            except MultipleResultsFound:
                logger.warning('Found multiple references from {}'.format(
                    ident['identifier']
                ))
                logger.debug('Cannot use {} for lookup as it is ambiguous'.format(ident['identifier']))
            except NoResultFound:
                pass
        else:
            return None

