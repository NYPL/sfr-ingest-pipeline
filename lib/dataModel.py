from Levenshtein import distance, jaro_winkler
from collections import defaultdict

class DataObject(object):
    def __init__(self):
        pass

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def getDictValue(self):
        return vars(self)

    @classmethod
    def createFromDict(cls, **kwargs):

        record = cls()
        for field, value in kwargs.items():
            record[field] = value

        return record


class WorkRecord(DataObject):
    def __init__(self, source=None):
        super()
        self.source = source
        self.identifiers = []
        self.instances = []
        self.subjects = []
        self.agents = []
        self.links = []
        self.measurements = []
        self.license = None
        self.language = None
        self.title = None
        self.subtitle = None
        self.altTitle = None
        self.rightsStatement = None
        self.issued = None
        self.published = None
        self.medium = None
        self.series = None
        self.seriesPosition = None
        self.primaryIdentifier = None

    def addIdentifier(self, **identifierDict):
        self.identifiers.append(Identifier.createFromDict(**identifierDict))

    def addInstance(self, **instanceDict):
        self.instances.append(InstanceRecord.createFromDict(**instanceDict))

    def addSubject(self, **subjectDict):
        self.subjects.append(Subject.createFromDict(**subjectDict))

    def addAgent(self, **agentDict):
        self.agents.append(Agent.createFromDict(**agentDict))

    def addMeasurement(self, **measurementDict):
        self.measurements.append(Measurement.createFromDict(**measurementDict))


class InstanceRecord(DataObject):
    def __init__(self, title=None, language=None):
        super()
        self.title = title
        self.language = language
        self.subtitle = None
        self.altTitle = None
        self.pubPlace = None
        self.pubDate = None
        self.edition = None
        self.editionStatement = None
        self.tableOfContents = None
        self.copyrightDate = None
        self.agents = None
        self.identifiers = []
        self.formats = []
        self.measurements = []


class Format(DataObject):
    def __init__(self, contentType=None, link=None, modified=None):
        super()
        self.contentType = contentType
        self.modified = modified
        self.drm = None
        self.measurements = []
        self.rightsURI = None
        self.link = None

        if (isinstance(link, Link)):
            self.link = link
        else:
            self.setLink(url=link)

    def setLink(self, **linkFields):
        newLink = Link.createFromDict(**linkFields)
        self.link = newLink


class Agent(DataObject):
    def __init__(self, name=None, role=None, aliases=None, birth=None, death=None, link=None):
        super()
        self.name = name
        self.sortName = None
        self.lcnaf = None
        self.viaf = None
        self.biography = None
        self.aliases = aliases
        self.birthDate = birth
        self.deathDate = death
        self.link = link

        if isinstance(role, (str, int)):
            self.roles = [role]
        else:
            self.roles = role

    # TODO This method is pretty ugly and there must be a better way to merge
    # agent records. However, it does work
    @staticmethod
    def checkForMatches(newAgents, agents):
        merged = defaultdict(dict)
        for agent in agents:
            merger = list(filter(lambda x: jaro_winkler(x['name'].lower(), agent['name'].lower()) > 0.8, newAgents))
            if(len(merger) > 0):
                mergedAgent = merger[0]
                merged[mergedAgent['name']] = Agent.mergeFromDict(agent, mergedAgent)
            else:
                merged[agent.name] = agent

        for newAgent in newAgents:
            if newAgent.name not in merged:
                merged[newAgent.name] = newAgent

        return merged.values()

    @staticmethod
    def mergeFromDict(otherAgent, agent):
        if isinstance(otherAgent, Agent):
            otherAgent = otherAgent.getDictValue()
        for key, value in otherAgent.items():
            if key == 'aliases' and agent.aliases is not None :
                agent['aliases'].extend(value)
                continue
            if key == 'roles':
                if isinstance(value, (str, int)):
                    value = [value]
                agent['roles'].extend(value)
            if agent[key] is None:
                agent[key] = value
        return agent


class Identifier(DataObject):
    def __init__(self, type=None, identifier=None, weight=None):
        super()
        self.type = type
        self.identifier = identifier
        self.weight = weight


class Link(DataObject):
    def __init__(self, url=None, mediaType=None, relType=None):
        super()
        self.url = url
        self.mediaType = mediaType
        self.content = None
        self.relType = None
        self.thumbnail = None


class Subject(DataObject):
    def __init__(self, subjectType=None, value=None, weight=None):
        super()
        self.type = subjectType
        self.identifier = None
        self.value = value
        self.weight = weight
        self.measurements = []


class Measurement(DataObject):
    def __init__(self, quantity=None, value=None, weight=None, takenAt=None):
        super()
        self.quantity = quantity
        self.value = value
        self.weight = weight
        self.takenAt = takenAt

    @staticmethod
    def getValueForMeasurement(measurementList, quantity):
        retMeasurement = list(filter(lambda x: x['quantity'] == quantity, measurementList))
        return retMeasurement[0]['value']
