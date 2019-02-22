from sqlalchemy import (
    Table,
    Column,
    Unicode,
    Integer,
    String,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
from sqlalchemy.orm.exc import NoResultFound
import pycountry

from model.core import Base, Core

from helpers.errorHelpers import DBError, DataError
from helpers.logHelpers import createLog

logger = createLog('languageModel')

WORK_LANGUAGE = Table(
    'work_language',
    Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id'), index=True),
    Column('language_id', Integer, ForeignKey('language.id'), index=True)
)

INSTANCE_LANGUAGE = Table(
    'instance_language',
    Base.metadata,
    Column('instance_id', Integer, ForeignKey('instances.id'), index=True),
    Column('language_id', Integer, ForeignKey('language.id'), index=True)
)


class Language(Core, Base):
    """A simple abstract language class that provides a representation of
    a language in a full-text and ISO 639-1/2 versions. This provides a robust
    lookup mechanism and allows SFR to handle languages in the vast majority
    of ways in which they are provided.

    @value language: Full-text representation of the language
    @value iso_2: ISO 639-1 2-letter language code
    @value iso_3: ISO 639-2 3-letter language code
    """

    __tablename__ = 'language'
    id = Column(Integer, primary_key=True)
    language = Column(Unicode, index=True)
    iso_2 = Column(String(2), index=True)
    iso_3 = Column(String(3), index=True)
    
    works = relationship(
        'Work',
        secondary=WORK_LANGUAGE,
        backref='language'
    )
    instances = relationship(
        'Instance',
        secondary=INSTANCE_LANGUAGE,
        backref='language'
    )

    def __repr__(self):
        return '<Language(lang={})>'.format(self.language)
    
    def __dir__(self):
        return ['language', 'iso_2', 'iso_3']