import os
from elasticsearch_dsl import (
    Index,
    Document,
    InnerDoc,
    Nested,
    Object,
    Keyword,
    Text,
    Integer,
    Short,
    Float,
    HalfFloat,
    Date,
    DateRange,
    Date,
    Boolean,
    analyzer
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


class MultiLanguage(InnerDoc):
    default = Text(
        analyzer='default',
        fields={'icu': Text(analyzer='icu_analyzer'), 'keyword': Keyword()}
    )
    ar = Text(analyzer='arabic')
    bg = Text(analyzer='bulgarian')
    bn = Text(analyzer='bengali')
    ca = Text(analyzer='catalan')
    cs = Text(analyzer='czech')
    da = Text(analyzer='danish')
    de = Text(analyzer='german')
    en = Text(analyzer='english')
    el = Text(analyzer='greek')
    es = Text(analyzer='spanish')
    eu = Text(analyzer='basque')
    fa = Text(analyzer='persian')
    fi = Text(analyzer='finnish')
    fr = Text(analyzer='french')
    gl = Text(analyzer='galician')
    hi = Text(analyzer='hindi')
    hu = Text(analyzer='hungarian')
    hy = Text(analyzer='armenian')
    id = Text(analyzer='indonesian')
    ir = Text(analyzer='irish')
    it = Text(analyzer='italian')
    ja = Text(analyzer='kuromoji') # japanese
    ko = Text(analyzer=analyzer(
        "korean",
        tokenizer='seunjeon_tokenizer'
    ))
    ku = Text(analyzer='sorani') # kurdish
    lt = Text(analyzer='lithuanian')
    lv = Text(analyzer='latvian')
    nl = Text(analyzer='dutch')
    no = Text(analyzer='norwegian')
    pl = Text(analyzer='polish')
    pt = Text(analyzer='portuguese')
    ro = Text(analyzer='romanian')
    ru = Text(analyzer='russian')
    sv = Text(analyzer='swedish')
    th = Text(analyzer='thai')
    tr = Text(analyzer='turkish')
    zh = Text(analyzer='smartcn') # chinese


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
    subject = Object(MultiLanguage)
    weight = HalfFloat()

    @classmethod
    def getFields(cls):
        return ['uri', 'authority']
    
    @classmethod
    def getLangFields(cls):
        return ['subject']


class Agent(BaseInner):
    name = Text(
        analyzer=analyzer(
            'plain_ascii',
            tokenizer='standard',
            filter=['standard', 'phonetic', 'lowercase', 'stop', 'asciifolding']
        ),
        fields={'keyword': Keyword()}
    )
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
    title = Object(MultiLanguage)
    sub_title = Object(MultiLanguage)
    pub_place = Text(fields={'keyword': Keyword()})
    pub_date = DateRange(format='date_optional_time')
    edition = Text(fields={'keyword': Keyword()})
    edition_statement = Object(MultiLanguage)
    table_of_contents = Object(MultiLanguage)
    volume = Object(MultiLanguage)
    extent = Text()
    summary =  Object(MultiLanguage)
    formats = Keyword()
    instance_id = Integer()
    edition_id = Integer()

    alt_titles = Nested(MultiLanguage)
    agents = Nested(Agent)
    identifiers = Nested(Identifier)
    rights = Nested(Rights)
    languages = Nested(Language)

    @classmethod
    def getFields(cls):
        return ['id', 'edition_id', 'pub_place', 'edition', 'extent']

    @classmethod
    def getLangFields(cls):
        return [
            'title', 'sub_title', 'edition_statement', 'table_of_contents',
            'volume', 'summary'
        ]

    def __dir__(self):
        return ['agents', 'identifiers', 'rights', 'languages', 'formats']
    
    def cleanRels(self):
        for rel in dir(self):
            if isinstance(getattr(self, rel), set):
                setattr(self, rel, list(getattr(self, rel)))


class Work(BaseDoc):
    title = Object(MultiLanguage)
    sort_title = Keyword(index=False)
    uuid = Keyword(store=True)
    medium = Text(fields={'keyword': Keyword()})
    series = Object(MultiLanguage)
    series_position = Keyword()
    issued_date = DateRange(format='date_optional_time')
    created_date = DateRange(format='date_optional_time')

    alt_titles = Nested(MultiLanguage)
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

    @classmethod
    def getLangFields(cls):
        return ['title', 'series']

    def __dir__(self):
        return ['identifiers', 'subjects', 'agents', 'languages']
    
    def __repr__(self):
        return '<ESWork(title={}, uuid={})>'.format(self.title.default, self.uuid)

    class Index:
        name = os.environ.get('ES_INDEX', None)
