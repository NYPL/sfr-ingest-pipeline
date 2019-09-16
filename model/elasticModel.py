import os
from elasticsearch_dsl import (
    Index,
    Document,
    InnerDoc,
    Nested,
    Keyword,
    Text,
    Integer,
    Short,
    Float,
    HalfFloat,
    Date,
    DateRange,
    Date,
    Boolean
)


class BaseDoc(Document):
    date_created = Date()
    date_modified = Date()

    def save(self, **kwargs):
        for rel in dir(self):
            if isinstance(getattr(self, rel), set):
                setattr(self, rel, list(getattr(self, rel)))
        return super().save(**kwargs)


class BaseInner(InnerDoc):
    date_created = Date()
    date_modified = Date()

    def save(self, **kwargs):
        for rel in dir(self):
            if isinstance(getattr(self, rel), set):
                setattr(self, rel, list(getattr(self, rel)))
        return super().save(**kwargs)


class Date(BaseInner):
    date = DateRange(format='date_optional_time')
    date_type = Keyword()


class Rights(BaseInner):
    source = Keyword()
    license = Keyword()
    rights_statement = Text(fields={'keyword': Keyword()})
    rights_reason = Text(fields={'keyword': Keyword()})

    @classmethod
    def getFields(cls):
        return ['source', 'license', 'rights_statement', 'rights_reason']

    def __key(self):
        return (self.source, self.license, self.rights_statement)

    def __hash__(self):
        return hash(self.__key())
    
    def __eq__(self, other):
        if isinstance(other, Rights):
            return self.__key() == other.__key()
        return NotImplemented


class Subject(BaseInner):
    authority = Keyword()
    uri = Keyword()
    subject = Text(fields={'keyword': Keyword()})
    weight = HalfFloat()

    @classmethod
    def getFields(cls):
        return ['uri', 'authority', 'subject']


class Agent(BaseInner):
    name = Text(fields={'keyword': Keyword()})
    sort_name = Keyword(index=False)
    aliases = Text(fields={'keyword': Keyword()})
    lcnaf = Keyword()
    viaf = Keyword()
    biography = Text()
    roles = Keyword()

    @classmethod
    def getFields(cls):
        return ['name', 'sort_name', 'lcnaf', 'viaf', 'biography']
    
    def __key(self):
        return (self.name, self.lcnaf, self.viaf)

    def __hash__(self):
        return hash(self.__key())
    
    def __eq__(self, other):
        if isinstance(other, Agent):
            return self.__key() == other.__key()
        return NotImplemented


class Identifier(BaseInner):
    id_type = Keyword()
    identifier = Keyword()

    def __key(self):
        return (self.id_type, self.identifier)

    def __hash__(self):
        return hash(self.__key())
    
    def __eq__(self, other):
        if isinstance(other, Identifier):
            return self.__key() == other.__key()
        return NotImplemented


class Language(BaseInner):
    language = Keyword()
    iso_2 = Keyword()
    iso_3 = Keyword()

    @classmethod
    def getFields(cls):
        return ['language', 'iso_2', 'iso_3']
    
    def __key(self):
        return (self.iso_3)

    def __hash__(self):
        return hash(self.__key())
    
    def __eq__(self, other):
        if isinstance(other, Language):
            return self.__key() == other.__key()
        return NotImplemented


class Instance(BaseInner):
    title = Text(fields={'keyword': Keyword()})
    sub_title = Text(fields={'keyword': Keyword()})
    alt_titles = Text(fields={'keyword': Keyword()})
    pub_place = Text(fields={'keyword': Keyword()})
    pub_date = DateRange(format='date_optional_time')
    edition = Text(fields={'keyword': Keyword()})
    edition_statement = Text(fields={'keyword': Keyword()})
    table_of_contents = Text()
    volume = Text(fields={'keyword': Keyword()})
    extent = Text()
    summary = Text() 
    formats = Keyword()
    instance_id = Integer()
    edition_id = Integer()

    agents = Nested(Agent)
    identifiers = Nested(Identifier)
    rights = Nested(Rights)
    languages = Nested(Language)

    @classmethod
    def getFields(cls):
        return [
            'id', 'edition_id', 'title', 'sub_title', 'pub_place', 'edition',
            'edition_statement', 'table_of_contents', 'extent', 'summary'
        ]

    def __dir__(self):
        return ['agents', 'identifiers', 'rights', 'languages', 'formats']
    
    def cleanRels(self):
        for rel in dir(self):
            if isinstance(getattr(self, rel), set):
                setattr(self, rel, list(getattr(self, rel)))


class Work(BaseDoc):
    title = Text(fields={'keyword': Keyword()})
    sort_title = Keyword(index=False)
    uuid = Keyword(store=True)
    medium = Text(fields={'keyword': Keyword()})
    series = Text(fields={'keyword': Keyword()})
    series_position = Keyword()
    alt_titles = Text(fields={'keyword': Keyword()})
    issued_date = DateRange(format='date_optional_time')
    created_date = DateRange(format='date_optional_time')

    instances = Nested(Instance)
    identifiers = Nested(Identifier)
    subjects = Nested(Subject)
    agents = Nested(Agent)
    languages = Nested(Language)
    
    @classmethod
    def getFields(cls):
        return [
            'uuid', 'title', 'sort_title', 'sub_title', 'medium',
            'series', 'series_position', 'date_modified', 'date_updated'
        ]
    
    def __dir__(self):
        return ['identifiers', 'subjects', 'agents', 'languages']
    
    def __repr__(self):
        return '<ESWork(title={}, uuid={})>'.format(self.title, self.uuid)

    class Index:
        name = os.environ.get('ES_INDEX', None)
