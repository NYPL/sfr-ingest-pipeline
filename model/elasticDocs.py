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
        return super(BaseDoc, self).save(**kwargs)


class BaseInner(InnerDoc):
    date_created = Date()
    date_modified = Date()

    def save(self, **kwargs):
        return super(BaseInner, self).save(**kwargs)


class Rights(BaseInner):
    source = Keyword()
    license = Keyword()
    rights_statement = Text(fields={'keyword': Keyword()})
    rights_reason = Text(fields={'keyword': Keyword()})
    copyright_date = DateRange()
    copyright_date_display = Keyword(index=False)
    determination_date = DateRange()
    determination_date_display = Keyword(index=False)

    @classmethod
    def getFields(cls):
        return ['source', 'license', 'rights_statement', 'rights_reason']    


class Measurement(BaseInner):
    quantity = Keyword()
    value = Float()
    weight = HalfFloat()
    taken_at = Date()

    @classmethod
    def getFields(cls):
        return ['quantity', 'value', 'weight', 'taken_at']


class AccessReport(BaseInner):
    ace_version = Keyword()
    score = HalfFloat()

    measurements = Nested(Measurement)

    @classmethod
    def getFields(cls):
        return ['ace_version', 'score']


class Subject(BaseInner):
    authority = Keyword()
    uri = Keyword()
    subject = Text(fields={'keyword': Keyword()})
    weight = HalfFloat()

    @classmethod
    def getFields(cls):
        return ['uri', 'authority', 'subject']


class Link(BaseInner):
    url = Keyword(index=False)
    media_type = Keyword()
    label = Text()
    local = Boolean()
    download = Boolean()
    images = Boolean()
    ebook = Boolean()
    thumbnail = Keyword(index=False)

    @classmethod
    def getFields(cls):
        return ['url', 'media_type', 'thumbnail']
    
    def setLabel(self, source, identifier=None):
        labelAddts = [source]
        if identifier: labelAddts.append(identifier)
        if self.ebook: labelAddts.append('eBook')
        if self.images: labelAddts.append('images')
        self.label = ' - '.join(labelAddts)


class Agent(BaseInner):
    name = Text(fields={'keyword': Keyword()})
    sort_name = Keyword(index=False)
    aliases = Text(fields={'keyword': Keyword()})
    lcnaf = Keyword()
    viaf = Keyword()
    birth_date = DateRange()
    birth_display = Keyword(index=False)
    death_date = DateRange()
    death_display = Keyword(index=False)
    biography = Text()
    roles = Keyword()

    links = Nested(Link)

    @classmethod
    def getFields(cls):
        return ['name', 'sort_name', 'lcnaf', 'viaf', 'biography']


class Identifier(BaseInner):
    id_type = Keyword()
    identifier = Keyword()


class Language(BaseInner):
    language = Keyword()
    iso_2 = Keyword()
    iso_3 = Keyword()

    @classmethod
    def getFields(cls):
        return ['language', 'iso_2', 'iso_3']


class Item(BaseInner):
    source = Keyword()
    content_type = Keyword()
    modified = Date()
    drm = Keyword()
    
    agents = Nested(Agent)
    measurements = Nested(Measurement)
    identifiers = Nested(Identifier)
    links = Nested(Link)
    access_reports = Nested(AccessReport)
    rights = Nested(Rights)

    @classmethod
    def getFields(cls):
        return ['source', 'content_type', 'modified', 'drm']


class Instance(BaseInner):
    title = Text(fields={'keyword': Keyword()})
    sub_title = Text(fields={'keyword': Keyword()})
    alt_titles = Text(fields={'keyword': Keyword()})
    pub_place = Text(fields={'keyword': Keyword()})
    pub_date = DateRange(format='date_optional_time')
    pub_date_display = Keyword(index=False)
    pub_date_sort = Date()
    pub_date_sort_desc = Date()
    edition = Text(fields={'keyword': Keyword()})
    edition_statement = Text(fields={'keyword': Keyword()})
    table_of_contents = Text()
    volume = Text(fields={'keyword': Keyword()})
    extent = Text()
    summary = Text()
    
    items = Nested(Item)
    agents = Nested(Agent)
    measurements = Nested(Measurement)
    identifiers = Nested(Identifier)
    links = Nested(Link)
    language = Nested(Language)
    rights = Nested(Rights)

    @classmethod
    def getFields(cls):
        return [
            'title', 'sub_title', 'pub_place', 'edition',
            'edition_statement', 'table_of_contents', 'langauge', 'extent',
            'volume', 'summary'
        ]


class Work(BaseDoc):
    title = Text(fields={'keyword': Keyword()})
    sort_title = Keyword(index=False)
    uuid = Keyword(store=True)
    medium = Text(fields={'keyword': Keyword()})
    series = Text(fields={'keyword': Keyword()})
    series_position = Keyword()
    issued = DateRange(format='date_optional_time')
    issued_display = Keyword(index=False)
    created = DateRange(format='date_optional_time')
    created_display = Keyword(index=False)
    alt_titles = Text(fields={'keyword': Keyword()})
    summary = Text()

    identifiers = Nested(Identifier)
    subjects = Nested(Subject)
    agents = Nested(Agent)
    measurements = Nested(Measurement)
    links = Nested(Link)
    instances = Nested(Instance)
    language = Nested(Language)
    rights = Nested(Rights)

    @classmethod
    def getFields(cls):
        return [
            'uuid', 'title', 'sort_title', 'sub_title', 'language', 'medium',
            'series', 'series_position', 'date_modified', 'date_updated'
        ]


    class Index:
        name = os.environ.get('ES_INDEX', None)
