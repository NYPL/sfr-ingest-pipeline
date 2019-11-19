import re
from collections import defaultdict

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Unicode,
    Table,
    func,
    text
)
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from .core import Base, Core

from ..helpers import createLog, DBError, DataError

logger = createLog('identifiers')

WORK_IDENTIFIERS = Table(
    'work_identifiers',
    Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id'), index=True),
    Column('identifier_id', Integer, ForeignKey('identifiers.id'), index=True)
)

INSTANCE_IDENTIFIERS = Table(
    'instance_identifiers',
    Base.metadata,
    Column('instance_id', Integer, ForeignKey('instances.id'), index=True),
    Column('identifier_id', Integer, ForeignKey('identifiers.id'), index=True)
)

ITEM_IDENTIFIERS = Table(
    'item_identifiers',
    Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id'), index=True),
    Column('identifier_id', Integer, ForeignKey('identifiers.id'), index=True)
)


class DOAB(Core, Base):
    """Table for DOAB Identifiers"""
    __tablename__ = 'doab'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True, unique=True)
    identifier_id = Column(Integer, ForeignKey('identifiers.id'), index=True)

    identifier = relationship('Identifier', back_populates='doab')

    def __repr__(self):
        return '<DOAB(value={})>'.format(self.value)


class Hathi(Core, Base):
    """Table for HathiTrust Identifiers"""
    __tablename__ = 'hathi'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True, unique=True)
    identifier_id = Column(Integer, ForeignKey('identifiers.id'), index=True)

    identifier = relationship('Identifier', back_populates='hathi')

    def __repr__(self):
        return '<Hathi(value={})>'.format(self.value)


class Gutenberg(Core, Base):
    """Table for Gutenberg Identifiers"""
    __tablename__ = 'gutenberg'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True, unique=True)
    identifier_id = Column(Integer, ForeignKey('identifiers.id'), index=True)

    identifier = relationship('Identifier', back_populates='gutenberg')

    def __repr__(self):
        return '<Gutenberg(value={})>'.format(self.value)


class OCLC(Core, Base):
    """Table for OCLC Identifiers"""
    __tablename__ = 'oclc'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True, unique=True)
    identifier_id = Column(Integer, ForeignKey('identifiers.id'), index=True)

    identifier = relationship('Identifier', back_populates='oclc')

    def __repr__(self):
        return '<OCLC(value={})>'.format(self.value)


class LCCN(Core, Base):
    """Table for Library of Congress Control Numbers"""
    __tablename__ = 'lccn'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True, unique=True)
    identifier_id = Column(Integer, ForeignKey('identifiers.id'), index=True)

    identifier = relationship('Identifier', back_populates='lccn')

    def __repr__(self):
        return '<LCCN(value={})>'.format(self.value)


class ISBN(Core, Base):
    """Table for ISBNs (10 and 13 digits)"""
    __tablename__ = 'isbn'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True, unique=True)
    identifier_id = Column(Integer, ForeignKey('identifiers.id'), index=True)

    identifier = relationship('Identifier', back_populates='isbn')

    def __repr__(self):
        return '<ISBN(value={})>'.format(self.value)


class OWI(Core, Base):
    """Table for OCLC Work Identifiers"""
    __tablename__ = 'owi'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True, unique=True)
    identifier_id = Column(Integer, ForeignKey('identifiers.id'), index=True)

    identifier = relationship('Identifier', back_populates='owi')

    def __repr__(self):
        return '<OWI(value={})>'.format(self.value)


class ISSN(Core, Base):
    """Table for ISSNs"""
    __tablename__ = 'issn'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True, unique=True)
    identifier_id = Column(Integer, ForeignKey('identifiers.id'), index=True)

    identifier = relationship('Identifier', back_populates='issn')

    def __repr__(self):
        return '<ISSN(value={})>'.format(self.value)


class LCC(Core, Base):
    """Table for Library of Congress Cataloging Numbers"""
    __tablename__ = 'lcc'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True, unique=True)
    identifier_id = Column(Integer, ForeignKey('identifiers.id'), index=True)

    identifier = relationship('Identifier', back_populates='lcc')

    def __repr__(self):
        return '<LCC(value={})>'.format(self.value)


class DDC(Core, Base):
    """Table for Dewey Decimal Control Numbers"""
    __tablename__ = 'ddc'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True, unique=True)
    identifier_id = Column(Integer, ForeignKey('identifiers.id'), index=True)

    identifier = relationship('Identifier', back_populates='ddc')

    def __repr__(self):
        return '<DDC(value={})>'.format(self.value)


class GENERIC(Core, Base):
    """Table for generic or otherwise uncontroller identifiers"""
    __tablename__ = 'generic'
    id = Column(Integer, primary_key=True)
    value = Column(Unicode, index=True, unique=True)
    identifier_id = Column(Integer, ForeignKey('identifiers.id'), index=True)

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
    doab = relationship('DOAB', back_populates='identifier')
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
        'doab': DOAB,
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
    def returnOrInsert(cls, session, identifier):
        """Manages either the creation or return of an existing identifier"""
        
        try:
            cls._cleanIdentifier(identifier)
        except DataError:
            return None

        try:
            return Identifier.lookupIdentifier(session, identifier)
        except NoResultFound:
            return Identifier.insert(identifier)

    @classmethod
    def insert(cls, iden):
        logger.debug('Inserting new identifier {} ({})'.format(
            iden['identifier'],
            iden['type']
        ))
        """Inserts a new identifier"""

        # Create a new entry in the core Identifier table
        coreIden = Identifier(type=iden['type'])

        # Load the model for the identifier type being stored
        specificIden = cls.identifierTypes[iden['type']]

        # Create new entry in that specific identifiers table
        idenRec = specificIden(value=iden['identifier'])

        # Add new identifier entry to the core table record
        idenTable = iden['type'] if iden['type'] is not None else 'generic'
        idenField = getattr(coreIden, idenTable)
        idenField.append(idenRec)

        return coreIden

    @classmethod
    def lookupIdentifier(cls, session, identifier):
        """Query database for a specific identifier. Return if found and
        raise an error if duplicate identifiers are found for a single
        type."""
        idenType = identifier['type']
        idenTable = idenType if idenType is not None else 'generic'
        
        return session.query(Identifier) \
            .join(idenTable) \
            .filter(
                cls.identifierTypes[idenType].value == identifier['identifier']
            ) \
            .one()
    
    @classmethod
    def getIdentiferRelationship(cls, session, identifier, model, recordID):
        idenType = identifier.type
        idenLookup = idenType if idenType is not None else 'generic'
        idenValue = getattr(identifier, idenLookup, 'generic')[0].value
        return session.query(model.id) \
            .join('identifiers', idenLookup) \
            .filter(cls.identifierTypes[idenType].value == idenValue) \
            .filter(model.id == recordID) \
            .one_or_none()

    @classmethod
    def getByIdentifier(cls, model, session, identifiers):
        """Query database for a record related to a specific identifier. Return
        if found and raise an error if multiple matching records are found."""

        className = model.__tablename__[:-1]

        cleanIdentifiers = []
        for i in identifiers:
            try:
                cleanIdentifiers.append(cls._cleanIdentifier(i))
            except DataError:
                continue

        idQueries = []
        for iden in cleanIdentifiers:
            logger.debug('Querying database for identifier {} ({})'.format(
                iden['identifier'],
                iden['type']
            ))
            idenType = iden['type']
            idenValue = iden['identifier']
            idQueries.append(
                'SELECT {}_id FROM {}_identifiers JOIN identifiers ON {}_identifiers.identifier_id = identifiers.id JOIN {} ON identifiers.id = {}.identifier_id WHERE {}.value=\'{}\''.format(
                    className, className, className, idenType, idenType, idenType, idenValue
                )
            )

        results = session.execute(text(' UNION ALL '.join(idQueries)))

        matches = defaultdict(int)
        for res in results:
            matches[res[0]] += 1

        sortedMatches = sorted(
            matches.items(),
            key=lambda x: x[1],
            reverse=True
        )

        if len(sortedMatches) > 0:
            return sortedMatches[0][0]

        return None

    @staticmethod
    def _cleanIdentifier(identifier):
        """Normalizes all identifiers received to remove issue ids"""

        identifierVal = str(identifier['identifier'])

        # Remove parenthetical notes on identifiers (Frequently found on ISBNs)
        cleanIdentifier = re.sub(r'\(.+\)', '', identifierVal).strip()

        # Block identifiers that consist of all zeros (A frequent test value)
        if re.match(r'^(?:nan|[0]+)$', cleanIdentifier, re.IGNORECASE):
            raise DataError('Non-unique identifier {} recieved'.format(
                cleanIdentifier
            ))

        return {
            'type': identifier['type'],
            'identifier': cleanIdentifier
        }
