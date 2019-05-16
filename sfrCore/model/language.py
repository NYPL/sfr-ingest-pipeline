from sqlalchemy import (
    Table,
    Column,
    Unicode,
    Integer,
    String,
    ForeignKey
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import text
from sqlalchemy.orm.exc import NoResultFound
import pycountry

from .core import Base, Core

from ..helpers import createLog, DBError, DataError

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
        backref=backref('language', collection_class=set)
    )
    instances = relationship(
        'Instance',
        secondary=INSTANCE_LANGUAGE,
        backref=backref('language', collection_class=set)
    )

    def __repr__(self):
        return '<Language(lang={})>'.format(self.language)
    
    def __dir__(self):
        return ['language', 'iso_2', 'iso_3']


    BAD_ISO_STRINGS = {
        'ger': 'deu',
        'fre': 'fra',
        'chi': 'zho',
        'wel': 'cym',
        'tib': 'bod',
        'alb': 'sqi',
        'slo': 'slk',
        'per': 'fas',
        'dut': 'nld',
        'ice': 'isl',
        'gre': 'ell',
        'cze': 'ces'
    }
    
    @classmethod
    def updateOrInsert(cls, session, language):
        
        logger.debug('Inserting or updating language {}'.format(str(language)))

        if language is None:
            raise DataError('Cannot parse None as language value')

        if isinstance(language, str):
            language = Language.loadFromString(language)
            if language is None: raise DataError('Unable to parse language')
        
        existing = Language.lookupLanguage(session, language)
        if existing: return existing

        logger.info('Inserting new language {}'.format(str(language)))
        return Language.insert(language)

    @classmethod
    def insert(cls, languageData):
        """Insert a new language row"""
        return Language(**languageData)

    @classmethod
    def lookupLanguage(cls, session, language):
        """Query database for language related to current record. Return language
        if found, otherwise return None"""
        return session.query(cls)\
            .filter(cls.language == language['language'])\
            .one_or_none()
    
    @classmethod
    def lookupRelLang(cls, session, lang, model, record):
        return session.query(cls)\
            .join(model.__tablename__)\
            .filter(cls.id == lang.id)\
            .filter(model.id == record.id)\
            .one_or_none()
    
    @classmethod
    def loadFromString(cls, lang):
        
        if lang in cls.BAD_ISO_STRINGS: lang = cls.BAD_ISO_STRINGS[lang]

        if len(lang) == 2:
            pyLang = pycountry.languages.get(alpha_2=lang.lower())
        elif len(lang) == 3:
            pyLang = pycountry.languages.get(alpha_3=lang.lower())
        else:
            pyLang = pycountry.languages.get(name=lang.capitalize())
        
        try:
            return {
                'language': pyLang.name,
                'iso_2': pyLang.alpha_2,
                'iso_3': pyLang.alpha_3
            }
        except AttributeError as err:
            logger.warning('Unable to parse language string {}'.format(lang))
            logger.debug(err)
            return None