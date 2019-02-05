from helpers.errorHelpers import DataError


class DataObject(object):
    """Abstract data model object that specific classes inherit from. Sets
    basic functions that allow writing/retrieving attributes."""

    def __init__(self):
        super()

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def getDictValue(self):
        """Convert current object into a dict. Used for generating JSON objects
        and in other instances where a standard type is necessary."""
        return vars(self)

    @classmethod
    def createFromDict(cls, **kwargs):
        """Take a standard dict object and convert to an instance of the
        provided class. Allows for creation of new instances with arbitrary
        fields set"""
        record = cls()
        for field, value in kwargs.items():
            if field not in dir(record):
                raise DataError('Field {} not valid for {}'.format(
                    field,
                    cls.__name__
                ))
            record[field] = value

        return record

    def addClassItem(self, listAttrib, classType, **identifierDict):
        if listAttrib not in dir(self):
            raise DataError('Field {} not valid for {}'.format(
                listAttrib,
                self.__class__.__name__
            ))
        self[listAttrib].append(classType.createFromDict(**identifierDict))


class WorkRecord(DataObject):
    def __init__(self):
        super()
        self.identifiers = []
        self.instances = []
        self.subjects = []
        self.agents = []
        self.links = []
        self.measurements = []
        self.dates = []
        self.uuid = None
        self.language = None
        self.title = None
        self.sub_title = None
        self.alt_titles = None
        self.sort_title = None
        self.medium = None
        self.series = None
        self.series_position = None
        self.primary_identifier = None
        self.rights = None

    def __repr__(self):
        dispTitle = self.title[:50] + '...' if self.title is not None and len(self.title) > 50 else self.title
        primaryID = None if self.primary_identifier is None else self.primary_identifier.identifier
        return '<Work(title={}, primary_id={})>'.format(
            dispTitle,
            primaryID
        )


class InstanceRecord(DataObject):
    def __init__(self, title=None, language=None):
        super()
        self.title = title
        self.language = language
        self.sub_title = None
        self.alt_titles = []
        self.pub_place = None
        self.edition = None
        self.edition_statement = None
        self.table_of_contents = None
        self.agents = []
        self.identifiers = []
        self.formats = []
        self.measurements = []
        self.dates = []
        self.rights = None

    def __repr__(self):
        dispTitle = self.title[:50] + '...' if self.title is not None and len(self.title) > 50 else self.title
        return '<Instance(title={}, pub_place={})>'.format(
            dispTitle,
            self.pub_place
        )


class Format(DataObject):
    def __init__(self, source=None, contentType=None, link=None, modified=None):
        super()
        self.source = source
        self.content_type = contentType
        self.modified = modified
        self.drm = None
        self.identifiers = []
        self.measurements = []
        self.links = []
        self.dates = []
        self.agents = []
        self.rights = None

        if link is not None:
            if (isinstance(link, Link)):
                self.links.append(link)
            else:
                self.setLink(url=link)

    def __repr__(self):
        return '<Item(type={}, source={})>'.format(
            self.content_type,
            self.source
        )

    def setLink(self, **linkFields):
        newLink = Link.createFromDict(**linkFields)
        self.links.append(newLink)


class Agent(DataObject):
    def __init__(self, name=None, role=None, aliases=None, link=None):
        super()
        self.name = name
        self.sort_name = None
        self.lcnaf = None
        self.viaf = None
        self.biography = None
        self.aliases = aliases
        self.link = link
        self.dates = []

        if isinstance(role, (str, int)):
            self.roles = [role]
        else:
            self.roles = role

    def __repr__(self):
        return '<Agent(name={}, roles={})>'.format(
            self.name,
            ', '.join(self.roles)
        )


class Identifier(DataObject):
    def __init__(self, type=None, identifier=None, weight=None):
        super()
        self.type = type
        self.identifier = identifier
        self.weight = weight

    def __repr__(self):
        return '<Identifier(type={}, id={})>'.format(
            self.type,
            self.identifier
        )


class Link(DataObject):
    def __init__(self, url=None, mediaType=None, relType=None):
        super()
        self.url = url
        self.media_type = mediaType
        self.content = None
        self.rel_type = None
        self.thumbnail = None

    def __repr__(self):
        return '<Link(url={}, type={})>'.format(self.url, self.media_type)


class Subject(DataObject):
    def __init__(self, subjectType=None, value=None, weight=None):
        super()
        self.authority = subjectType
        self.subject = value
        self.uri = None
        self.weight = weight
        self.measurements = []

    def __repr__(self):
        return '<Subject(authority={}, subject={})>'.format(
            self.authority,
            self.subject
        )


class Measurement(DataObject):
    def __init__(self, quantity=None, value=None, weight=None, takenAt=None):
        super()
        self.quantity = quantity
        self.value = value
        self.weight = weight
        self.taken_at = takenAt

    def __repr__(self):
        return '<Measurement(quantity={}, value={})>'.format(
            self.quantity,
            self.value
        )

    @staticmethod
    def getValueForMeasurement(measurementList, quantity):
        retMeasurement = list(filter(lambda x: x['quantity'] == quantity, measurementList))
        return retMeasurement[0]['value']


class Date(DataObject):
    def __init__(self, displayDate=None, dateRange=None, dateType=None):
        super()
        self.display_date = displayDate
        self.date_range = dateRange
        self.date_type = dateType

    def __repr__(self):
        return '<Date(date={}, type={})>'.format(
            self.display_date,
            self.date_type
        )


class Rights(DataObject):
    def __init__(self, source=None, license=None, statement=None, reason=None):
        super()
        self.source = source
        self.license = license
        self.rights_statement = statement
        self.rights_reason = reason
        self.dates = []

    def __repr__(self):
        return '<Rights(license={})>'.format(self.license)
