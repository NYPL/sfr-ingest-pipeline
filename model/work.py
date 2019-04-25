import uuid
import json
from sqlalchemy import (
    Column,
    Date,
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

from model.core import Base, Core
from model.subject import SUBJECT_WORKS
from model.identifiers import WORK_IDENTIFIERS, Identifier
from model.altTitle import AltTitle, WORK_ALTS
from model.rawData import RawData
from model.measurement import WORK_MEASUREMENTS, Measurement
from model.link import WORK_LINKS, Link
from model.date import DateField
from model.instance import Instance
from model.agent import Agent
from model.subject import Subject
from model.language import Language

from helpers.errorHelpers import DBError, DataError
from helpers.logHelpers import createLog

logger = createLog('workModel')


#
# The root-level SFR record of Work corresponds to the FRBR and BIBFRAME
# concepts at the same level.
#
class Work(Core, Base):
    """The highest level FRBR entity, a work encodes the data about the
    intellectual content of an entity. This includes things such as title,
    author and, importantly, copyright data. The work also includes
    relationships to agents, instances, alternate titles, links and
    measurements"""
    __tablename__ = 'works'
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False)
    title = Column(Unicode, index=True)
    sort_title = Column(Unicode, index=True)
    sub_title = Column(Unicode, index=True)
    medium = Column(Unicode)
    series = Column(Unicode)
    series_position = Column(Unicode)
    summary = Column(Unicode)

    #
    # Relationships
    #

    alt_titles = relationship(
        'AltTitle',
        secondary=WORK_ALTS,
        back_populates='work'
    )
    subjects = relationship(
        'Subject',
        secondary=SUBJECT_WORKS,
        back_populates='work'
    )
    instances = relationship(
        'Instance',
        back_populates='work'
    )
    agents = association_proxy(
        'agent_works',
        'agent'
    )
    measurements = relationship(
        'Measurement',
        secondary=WORK_MEASUREMENTS,
        back_populates='work'
    )
    identifiers = relationship(
        'Identifier',
        secondary=WORK_IDENTIFIERS,
        back_populates='work'
    )
    links = relationship(
        'Link',
        secondary=WORK_LINKS,
        back_populates='works'
    )
    
    import_json = relationship(
        'RawData',
        back_populates='work'
    )

    CHILD_FIELDS = [
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

    def __repr__(self):
        return '<Work(title={})>'.format(self.title)

    @classmethod
    def _buildChildDict(cls, workData):
        return { field: workData.pop(field, []) for field in cls.CHILD_FIELDS }

    @classmethod
    def insert(cls, session, workData):
        """Insert a new work record"""
        logger.info('Inserting new work record {}'.format(workData['title']))

        # TODO Remove prepositions, etc from the start of the sort title
        workData['sort_title'] = workData.get('sort_title', workData['title'])
        
        childFields = Work._buildChildDict(workData)

        work = cls(**workData)
        session.add(work)
        #
        # === IMPORTANT ===
        # This inserts a uuid value for the db row
        # This might want to be a namespaced UUID in the future, but for now
        # it will be a random v4 value
        #
        work.uuid = uuid.uuid4()

        jsonRec = RawData(data=childFields['storeJson'])
        work.import_json.append(jsonRec)
        
        Work._addIdentifiers(session, work, childFields['identifiers'])
        
        Work._addInstances(session, work, childFields['instances'])

        Work._addAgents(session, work, childFields['agents'])

        Work._addAltTitles(work, childFields['alt_titles'])

        Work._addSubjects(session, work, childFields['subjects'])

        Work._addMeasurements(session, work, childFields['measurements'])

        Work._addLinks(work, childFields['links'])

        Work._addDates(work, childFields['dates'])

        Work._addLanguages(session, work, childFields['language'])
                
        return work
    
    @classmethod
    def _addInstances(cls, session, work, instances):
        for instance in instances:
            instanceRec = Instance.insert(session, instance)
            work.instances.append(instanceRec)
    
    @classmethod
    def _addIdentifiers(cls, session, work, identifiers):
        for iden in identifiers:
            try:
                status, idenRec = Identifier.returnOrInsert(
                    session,
                    iden
                )
                work.identifiers.append(idenRec)
            except DataError as err:
                logger.warning('Received invalid identifier')
                logger.debug(err)
    
    @classmethod
    def _addAgents(cls, session, work, agents):
        relsCreated = []
        for agent in agents:
            try:
                agentRec, roles = Agent.updateOrInsert(session, agent)
                for role in roles:
                    if (agentRec.name, role) in relsCreated: continue
                    relsCreated.append((agentRec.name, role))
                    AgentWorks(
                        agent=agentRec,
                        work=work,
                        role=role
                    )
            except DataError:
                logger.warning('Unable to read agent {}'.format(agent['name']))
    
    @classmethod
    def _addAltTitles(cls, work, altTitles):
        if altTitles is not None:
            # Quick conversion to set to eliminate duplicate alternate titles
            for altTitle in list(set(altTitles)):
                work.alt_titles.append(AltTitle(title=altTitle))
    
    @classmethod
    def _addSubjects(cls, session, work, subjects):
        for subject in set(subjects):
            op, subjectRec = Subject.updateOrInsert(session, subject)
            work.subjects.append(subjectRec)

    @classmethod
    def _addMeasurements(cls, session, work, measurements):
        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            work.measurements.append(measurementRec)
    
    @classmethod
    def _addLinks(cls, work, links):
        for link in links:
            newLink = Link(**link)
            work.links.append(newLink)
    
    @classmethod
    def _addDates(cls, work, dates):
        for date in dates:
            newDate = DateField.insert(date)
            work.dates.append(newDate)
    
    @classmethod
    def _addLanguages(cls, session, work, languages):
        if languages is not None:
            if isinstance(languages, str):
                languages = [languages]
            
            for lang in languages:
                try:
                    newLang = Language.updateOrInsert(session, lang)
                    work.language.append(newLang)
                except DataError:
                    logger.debug('Unable to parse language {}'.format(lang))
                    continue
    
    @classmethod
    def lookupWork(cls, session, identifiers, primaryIdentifier=None):
        """Lookup a work either by UUID or by another identifier"""
        if primaryIdentifier is not None and primaryIdentifier['type'] == 'uuid':
            return Work.getByUUID(session, primaryIdentifier['identifier'])

        existingWorkID = Identifier.getByIdentifier(Work, session, identifiers)
        if existingWorkID:
            return session.query(Work).get(existingWorkID).uuid
        else:
            existingInstanceID = Identifier.getByIdentifier(Instance, session, identifiers)
            if existingInstanceID:
                return session.query(Instance).get(existingInstanceID).work.uuid
        
        return None

    @classmethod
    def getByUUID(cls, session, recUUID):
        """Query the database for a work by UUID. Returns only one record or
        errors. (If duplicate UUIDs exist, a serious error has occured)"""
        qUUID = uuid.UUID(recUUID)
        try:
            existing = session.query(Work.uuid)\
                .filter(Work.uuid == qUUID)\
                .one()
        except NoResultFound:
            logger.error('No matching UUID {} found!'.format(recUUID))
            raise DBError('work', 'Original UUID {} not found, check error logs'.format(
                recUUID
            ))
        return existing


class AgentWorks(Core, Base):
    """Table relating agents and works. Is instantiated as a class to
    allow the assigning of a 'role' to each relationship.
    (e.g. author, editor)"""

    __tablename__ = 'agent_works'
    work_id = Column(Integer, ForeignKey('works.id'), primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), primary_key=True)
    role = Column(String(64), primary_key=True)

    agentWorksPkey = PrimaryKeyConstraint(
        'work_id',
        'agent_id',
        'role',
        name='agent_works_pkey'
    )

    work = relationship(
        Work,
        backref=backref('agent_works', cascade='all, delete-orphan')
    )
    agent = relationship('Agent')

    def __repr__(self):
        return '<AgentWorks(work={}, agent={}, role={})>'.format(
            self.work_id,
            self.agent_id,
            self.role
        )

    @classmethod
    def roleExists(cls, session, agent, role, recordID):
        """Query database to check if a role exists between a specific work and
        agent"""
        return session.query(cls)\
            .filter(cls.agent_id == agent.id)\
            .filter(cls.work_id == recordID)\
            .filter(cls.role == role)\
            .one_or_none()
