from collections import defaultdict
import re
import uuid
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Unicode,
    PrimaryKeyConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.exc import NoResultFound

from .core import Base, Core
from .subject import SUBJECT_WORKS
from .identifiers import WORK_IDENTIFIERS, Identifier
from .altTitle import AltTitle, WORK_ALTS
from .rawData import RawData
from .measurement import WORK_MEASUREMENTS, Measurement
from .link import WORK_LINKS, Link
from .date import DateField
from .instance import Instance
from .agent import Agent
from .subject import Subject
from .language import Language

from ..helpers import createLog, DBError, DataError

logger = createLog('workModel')


class Work(Core, Base):
    """The highest level FRBR entity, a work encodes the data about the
    intellectual content of an entity. This includes things such as title,
    author and, importantly, copyright data. The work also includes
    relationships to agents, instances, alternate titles, links and
    measurements"""
    __tablename__ = 'works'
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    title = Column(Unicode, index=True)
    sort_title = Column(Unicode, index=True)
    sub_title = Column(Unicode)
    medium = Column(Unicode)
    series = Column(Unicode)
    series_position = Column(Unicode)

    alt_titles = relationship(
        'AltTitle',
        secondary=WORK_ALTS,
        back_populates='work',
        collection_class=set
    )
    subjects = relationship(
        'Subject',
        secondary=SUBJECT_WORKS,
        back_populates='work',
        collection_class=set
    )
    instances = relationship(
        'Instance',
        back_populates='work',
        collection_class=set
    )
    agents = association_proxy(
        'agent_works',
        'agent',
        creator=lambda x: AgentWorks(
            agent=x['agent'],
            work=x['work'],
            role=x['role']
        )
    )
    measurements = relationship(
        'Measurement',
        secondary=WORK_MEASUREMENTS,
        back_populates='work',
        collection_class=set
    )
    identifiers = relationship(
        'Identifier',
        secondary=WORK_IDENTIFIERS,
        back_populates='work',
        collection_class=set
    )
    links = relationship(
        'Link',
        secondary=WORK_LINKS,
        back_populates='works',
        collection_class=set
    )
    import_json = relationship(
        'RawData',
        back_populates='work'
    )

    RELS = [
        'instances',
        'identifiers',
        'agents',
        'alt_titles',
        'subjects',
        'measurements',
        'links',
        'storeJson',
        'dates',
        'rights',
        'language'
    ]

    def __init__(self, session=None):
        self.session = session

    def __repr__(self):
        return '<Work(title={})>'.format(self.title)

    def createTmpRelations(self, workData):
        logger.debug('Creating tmp relationship arrays')
        for relType in Work.RELS:
            tmpRel = 'tmp_{}'.format(relType)
            relList = workData.pop(relType, [])
            if relList is None:
                relList = []
            elif isinstance(relList, str):
                relList = [relList]
            dedupeList = [
                val for pos, val in enumerate(relList)
                if val not in relList[pos + 1:]
            ]
            setattr(self, tmpRel, dedupeList)

    def removeTmpRelations(self):
        """Removes temporary attributes that were used to hold related objects.
        """
        logger.debug('Removing temporary relationship arrays')
        for rel in Work.RELS:
            delattr(self, 'tmp_{}'.format(rel))

    def insert(self, workData):
        """Insert a new work record"""
        logger.info('Inserting new work record {}'.format(workData['title']))

        self.createTmpRelations(workData)

        for key, value in workData.items():
            logger.debug('Setting {} for field {}'.format(value, key))
            setattr(self, key, value)

        #
        # === IMPORTANT ===
        # This inserts a uuid value for the db row
        # This might want to be a namespaced UUID in the future, but for now
        # it will be a random v4 value
        #
        self.uuid = uuid.uuid4()

        logger.debug('Adding current work {} to session'.format(self))
        self.session.add(self)

        self.addImportJson()
        self.addIdentifiers()
        self.addInstances()
        self.addAgents()
        self.addAltTitles()
        self.addSubjects()
        self.addMeasurements()
        self.addLinks()
        self.addDates()
        self.addLanguages()

        if self.sort_title is None:
            logger.debug('Setting sort_title to {}'.format(self.title))
            self.sort_title = self.setSortTitle()

        epubsToLoad = getattr(self, 'epubsToLoad', [])
        delattr(self, 'epubsToLoad')
        delattr(self, 'session')
        self.removeTmpRelations()

        return epubsToLoad

    def update(self, workData, session=None):
        """Update an existing work record"""
        logger.info('Updating existing work record {}'.format(self.id))
        if not getattr(self, 'session', None):
            self.session = session

        self.createTmpRelations(workData)

        for field, value in workData.items():
            if (
                value is not None
                and value.strip() != ''
                and field != 'title'
            ):
                logger.debug('Setting {} for field {}'.format(value, field))
                setattr(self, field, value)

        self.addImportJson()
        self.addTitles(workData.get('title', ''))
        self.updateIdentifiers()
        self.updateInstances()
        self.updateAgents()
        self.updateSubjects()
        self.updateMeasurements()
        self.updateLinks()
        self.updateDates()
        self.updateLanguages()

        epubsToLoad = getattr(self, 'epubsToLoad', [])
        delattr(self, 'epubsToLoad')
        delattr(self, 'session')
        self.removeTmpRelations()

        return epubsToLoad

    def addImportJson(self):
        logger.debug('Adding JSON block of current import data')
        self.import_json.append(RawData(data=self.tmp_storeJson))

    def addIdentifiers(self):
        logger.info('Adding identifiers to work')
        self.identifiers = {
            self.addIdentifier(i) for i in self.tmp_identifiers
        }

    def addIdentifier(self, iden):
        try:
            return Identifier.returnOrInsert(self.session, iden)
        except DataError as err:
            logger.warning('Received invalid identifier')
            logger.debug(err)

    def updateIdentifiers(self):
        logger.info('Upserting identifiers for work')
        for iden in self.tmp_identifiers:
            self.updateIdentifier(iden)

    def updateIdentifier(self, iden):
        try:
            self.identifiers.add(Identifier.returnOrInsert(self.session, iden))
        except DataError as err:
            logger.warning('Received invalid identifier')
            logger.debug(err)

    def addInstances(self):
        logger.info('Adding instances to work')
        self.epubsToLoad = []
        for inst in self.tmp_instances:
            self.addInstance(inst)

    def addInstance(self, instance):
        newInstance, newEpubs = Instance.createNew(self.session, instance)
        self.instances.add(newInstance)
        self.epubsToLoad.extend(newEpubs)
        return newInstance

    def updateInstances(self):
        logger.info('Upserting instances for work')
        self.epubsToLoad = []
        instIDs = self.getLocalInstanceIdentifiers()
        for instance in self.tmp_instances:
            existing = self.matchLocalInstance(instance, instIDs)
            if existing:
                self.updateInstance(existing, instance)
                self.addNewIdentifiers(existing, instIDs)
            else:
                new = self.addInstance(instance)
                self.addNewIdentifiers(new, instIDs)

    def updateInstance(self, existing, newInst):
        try:
            epubsToLoad = existing.update(self.session, newInst)
            self.epubsToLoad.extend(epubsToLoad)
        except (DataError, DBError) as err:
            logger.warning('Unable to upsert instance record')
            logger.debug(err)

    def getLocalInstanceIdentifiers(self):
        instDict = {}
        for inst in self.instances:
            self.addNewIdentifiers(inst, instDict)
        return instDict

    def addNewIdentifiers(self, instance, instDict):
        for iden in instance.identifiers:
            idType = iden.type if iden.type else 'generic'
            if idType in ['ddc', 'lcc']:
                continue
            idRec = getattr(iden, idType)[0]
            value = getattr(idRec, 'value')
            idKey = '{}/{}'.format(idType, value)
            instDict[idKey] = instance

    def matchLocalInstance(self, inst, instDict):
        matches = defaultdict(int)
        for iden in inst['identifiers']:
            idKey = '{}/{}'.format(iden['type'], iden['identifier'])
            try:
                matchInst = instDict[idKey]
                logger.debug('Found match to {} on {}'.format(
                    matchInst, idKey
                ))
            except KeyError:
                continue

            matches[matchInst] += 1

        sortedMatches = sorted(
            matches.items(),
            key=lambda x: x[1],
            reverse=True
        )
        if len(sortedMatches) > 0:
            logger.info('Matched new instance to {}'.format(
                sortedMatches[0][0]
            ))
            return sortedMatches[0][0]

        return None

    def addAgents(self):
        logger.info('Adding agents to work')
        for a in self.tmp_agents:
            self.addAgent(a)

    def addAgent(self, agent):
        try:
            agentRec, roles = Agent.updateOrInsert(self.session, agent)
            if roles is None:
                roles = ['author']
            self.agents.extend = {
                AgentWorks(agent=agentRec, work=self, role=role)
                for role in set(roles)
            }
        except (DataError, DBError) as err:
            logger.warning('Unable to read agent {}'.format(agent['name']))
            logger.debug(err)

    def updateAgents(self):
        logger.info('Upserting agents for work')
        for agent in self.tmp_agents:
            self.updateAgent(agent)

    def updateAgent(self, agent):
        try:
            agentRec, roles = Agent.updateOrInsert(self.session, agent)
            if roles is None:
                roles = ['author']
            for role in roles:
                if AgentWorks.roleExists(
                    self.session,
                    agentRec,
                    role,
                    self.id
                ) is None:
                    AgentWorks(agent=agentRec, work=self, role=role)
        except (DataError, DBError) as err:
            logger.warning('Unable to read agent {}'.format(agent['name']))
            logger.debug(err)

    def addSubjects(self):
        logger.info('Adding subjects to work')
        self.subjects = {
            Subject.updateOrInsert(self.session, s)
            for s in self.tmp_subjects
        }

    def updateSubjects(self):
        logger.info('Upserting subjects for work')
        for subject in self.tmp_subjects:
            self.updateSubject(subject)

    def updateSubject(self, subj):
        self.subjects.add(Subject.updateOrInsert(self.session, subj))

    def addMeasurements(self):
        self.measurements = {
            Measurement.insert(m) for m in self.tmp_measurements
        }

    def updateMeasurements(self):
        for measurement in self.tmp_measurements:
            self.updateMeasurement(measurement)

    def updateMeasurement(self, measure):
        self.measurements.add(
            Measurement.updateOrInsert(self.session, measure, Work, self.id)
        )

    def addLinks(self):
        self.links = {Link(**l) for l in self.tmp_links}

    def updateLinks(self):
        for link in self.tmp_links:
            self.updateLink(link)

    def updateLink(self, link):
        self.links.add(Link.updateOrInsert(self.session, link, Work, self.id))

    def addDates(self):
        self.dates = {DateField.insert(d) for d in self.tmp_dates}

    def updateDates(self):
        for date in self.tmp_dates:
            self.updateDate(date)

    def updateDate(self, date):
        self.dates.add(
            DateField.updateOrInsert(self.session, date, Work, self.id)
        )

    def addLanguages(self):
        if self.tmp_language is not None:
            if isinstance(self.tmp_language, str):
                self.tmp_language = [self.tmp_language]

            for lang in self.tmp_language:
                print(self.addLanguage(lang))
                self.language.update(self.addLanguage(lang))

    def addLanguage(self, language):
        try:
            return Language.updateOrInsert(self.session, language)
        except DataError:
            logger.debug('Unable to parse language {}'.format(language))

    def updateLanguages(self):
        if self.tmp_language is not None:
            if isinstance(self.tmp_language, str):
                self.tmp_language = [self.tmp_language]

            for lang in self.tmp_language:
                self.updateLanguage(lang)

    def updateLanguage(self, lang):
        self.language.update(self.addLanguage(lang))

    def addAltTitles(self):
        self.alt_titles = {AltTitle(title=a) for a in self.tmp_alt_titles}

    def addTitles(self, newTitle):

        # The "canonical title" should be the record with the most holdings
        if newTitle.lower() != self.title.lower():
            newHoldings = list(filter(
                lambda x: x['quantity'] == 'holdings',
                self.tmp_measurements
            ))
            if len(newHoldings) >= 1:
                newHoldings = newHoldings[0]['value']

                oldHoldings = Measurement.getMeasurements(
                    self.session,
                    'holdings',
                    Work,
                    self.id
                )

                if not all(float(h) > float(newHoldings) for h in oldHoldings):
                    AltTitle.insertOrSkip(
                        self.session,
                        self.title,
                        Work,
                        self.id
                    )
                    self.title = newTitle
                    self.setSortTitle()
                else:
                    AltTitle.insertOrSkip(
                        self.session, newTitle, Work, self.id
                    )

        if self.tmp_alt_titles:
            for a in self.tmp_alt_titles:
                newAlt = AltTitle.insertOrSkip(self.session, a, Work, self.id)
                if newAlt:
                    self.alt_titles.add(newAlt)

    def setSortTitle(self):
        workLangs = [l.iso_3 for l in list(self.language)]

        stops = Work.getStops(workLangs)

        titleTokens = re.split(r'\s+', self.title)
        stoppedTitle = []
        for i, t in enumerate(titleTokens):
            if t.lower() in stops:
                continue
            else:
                stoppedTitle = titleTokens[i:]
                break
        self.sort_title = ' '.join(stoppedTitle).lower()

    @staticmethod
    def getStops(workLangs):
        eng_stops = ['a', 'an', 'the']
        fra_stops = ['le', 'la', 'les', 'l', 'un', 'une']
        esp_stops = ['el', 'la', 'los', 'las', 'un', 'una']

        lang_stops = {
            'eng': eng_stops,
            'fra': fra_stops,
            'esp': esp_stops
        }
        for lang in workLangs:
            try:
                return lang_stops[lang]
            except KeyError:
                continue

        return lang_stops['eng']

    @classmethod
    def lookupWork(cls, session, identifiers, primaryID=None):
        """Lookup a work either by UUID or by another identifier"""
        if primaryID is not None and primaryID['type'] == 'uuid':
            return Work.getByUUID(session, primaryID['identifier'])

        workID = Identifier.getByIdentifier(Work, session, identifiers)
        if not workID:
            instanceID = Identifier.getByIdentifier(
                Instance,
                session,
                identifiers
            )
            if instanceID:
                workID = session.query(Instance.work_id)\
                    .filter(Instance.id == instanceID).one()[0]

        if workID:
            return session.query(Work).get(workID)
        return None

    @classmethod
    def getByUUID(cls, session, recUUID):
        """Query the database for a work by UUID. Returns only one record or
        errors. (If duplicate UUIDs exist, a serious error has occurred)"""
        try:
            return session.query(Work)\
                .filter(Work.uuid == uuid.UUID(recUUID))\
                .one()
        except NoResultFound:
            logger.error('No matching UUID {} found!'.format(recUUID))
            raise DBError(
                'work',
                'Original UUID {} not found, check error logs'.format(recUUID)
            )

    @classmethod
    def lookupSubjectRel(cls, session, subject, workID):
        """Query database for a subject record related to the current work"""
        return session.query(cls)\
            .join('subjects')\
            .filter(Subject.subject == subject.subject)\
            .filter(cls.id == workID)\
            .one_or_none()

    def importSubjects(self, session, subjects):
        for subject in subjects:
            self.subjects.add(Subject.updateOrInsert(session, subject))


class AgentWorks(Core, Base):
    """Table relating agents and works. Is instantiated as a class to
    allow the assigning of a 'role' to each relationship.
    (e.g. author, editor)"""

    __tablename__ = 'agent_works'
    work_id = Column(
        Integer, ForeignKey('works.id'), primary_key=True, index=True
    )
    agent_id = Column(
        Integer, ForeignKey('agents.id'), primary_key=True, index=True
    )
    role = Column(String(64), primary_key=True)

    agentWorksPkey = PrimaryKeyConstraint(
        'work_id',
        'agent_id',
        'role',
        name='agent_works_pkey'
    )

    work = relationship(
        Work,
        backref=backref(
            'agent_works',
            collection_class=set,
            cascade='all, delete-orphan'
        )
    )
    agent = relationship('Agent')

    def __init__(self, work=None, agent=None, role=None):
        self.work = work
        self.agent = agent
        self.role = role

    def __repr__(self):
        return '<AgentWorks(work={}, agent={}, role={})>'.format(
            self.work_id,
            self.agent_id,
            self.role
        )

    @classmethod
    def roleExists(cls, session, agent, role, recordID):
        """Query database to see if relationship with role exists between
        agent and work. Returns model work if it does or None if it
        does not"""
        return session.query(cls)\
            .filter(cls.agent_id == agent.id)\
            .filter(cls.work_id == recordID)\
            .filter(cls.role == role)\
            .one_or_none()
