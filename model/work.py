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
from model.rights import Rights, WORK_RIGHTS
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
        'agent'
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
    def update(cls, session, existing, work):
        """Update an existing work record"""
        logger.debug('Updating existing work record {}'.format(existing.id))

        childFields = Work._buildChildDict(work)

        jsonRec = RawData(data=childFields['storeJson'])
        existing.import_json.append(jsonRec)

        for field, value in work.items():
            if (
                value is not None
                and value.strip() != ''
                and field != 'title'
            ):
                setattr(existing, field, value)

        Work._addTitles(
            session,
            work,
            existing,
            childFields['measurements'],
            childFields['alt_titles']
        )

        Work._addIdentifiers(session, existing, childFields['identifiers'])
        
        Work._addInstances(session, existing, childFields['instances'])

        Work._addAgents(session, existing, childFields['agents'])

        Work._addSubjects(session, existing, childFields['subjects'])

        Work._addMeasurements(session, existing, childFields['measurements'])

        Work._addLinks(session, existing, childFields['links'])

        Work._addDates(session, existing, childFields['dates'])
        
        Work._addLanguages(session, existing, childFields['language'])

        return existing

    @classmethod
    def _addTitles(cls, session, work, existing, measurements, altTitles):
        newTitle = work.get('title')
        if altTitles is None:
            altTitles = []
        # The "canonical title" should be set to the record with the most holdings
        if newTitle.lower() != existing.title.lower():
            newHoldings = list(filter(lambda x: x['quantity'] == 'holdings', measurements))
            if len(newHoldings) >= 1:
                newHoldings = newHoldings[0]

                oldHoldings = Measurement.getMeasurements(
                    session,
                    'holdings',
                    Work,
                    existing.id
                )

                for holding in oldHoldings:
                    try:
                        if float(newHoldings['value']) > float(holding):
                            altTitles.append(existing.title)
                            existing.title = newTitle
                            break
                    except TypeError:
                        pass
                else:
                    altTitles.append(newTitle)

        # Handle adding alt_titles
        altTitles = {
            AltTitle.insertOrSkip(session, a, Work, existing.id)
            for a in altTitles
        }
        existing.alt_titles.update(list(filter(None, altTitles)))
    
    @classmethod
    def _addInstances(cls, session, existing, instances):
        for instance in instances:
            existing.instances.add(Instance.updateOrInsert(
                session,
                instance, 
                work=existing
            ))

    @classmethod
    def _addIdentifiers(cls, session, existing, identifiers):
        for iden in identifiers:
            try:
                existing.identifiers.add(
                    Identifier.returnOrInsert(session, iden)
                )        
            except DataError as err:
                logger.warning('Received invalid identifier')
                logger.debug(err)
    
    @classmethod
    def _addAgents(cls, session, existing, agents):
        for agent in agents:
            try:
                agentRec, roles = Agent.updateOrInsert(session, agent)
                if roles is None:
                    roles = ['author']
                for role in roles:
                    if AgentWorks.roleExists(session, agentRec, role, existing.id) is None:
                        AgentWorks(
                            agent=agentRec,
                            work=existing,
                            role=role
                        )
            except DataError:
                logger.warning('Unable to read agent {}'.format(agent['name']))
    
    @classmethod
    def _addSubjects(cls, session, existing, subjects):
        for subject in subjects:
            existing.subjects.add(
                Subject.updateOrInsert(session, subject)
            )
    
    @classmethod
    def _addMeasurements(cls, session, existing, measurements):
        for measurement in measurements:
            existing.measurements.add(
                Measurement.updateOrInsert(
                    session,
                    measurement,
                    Work,
                    existing.id
                )
            )

    @classmethod
    def _addLinks(cls, session, existing, links):
        for link in links:
            existing.links.add(
                Link.updateOrInsert(session, link, Work, existing.id)
            )
    
    @classmethod
    def _addDates(cls, session, existing, dates):
        for date in dates:
            existing.dates.add(
                DateField.updateOrInsert(session, date, Work, existing.id)
            )
    
    @classmethod
    def _addLanguages(cls, session, existing, languages):
        if languages is not None:
            if isinstance(languages, str):
                languages = [languages]

            for lang in languages:
                try:
                    existing.language.add(
                        Language.updateOrInsert(session, lang)
                    )
                except DataError:
                    logger.warning('Unable to parse language {}'.format(lang))

    @classmethod
    def lookupWork(cls, session, identifiers, primaryIdentifier=None):
        """Lookup a work either by UUID or by another identifier"""
        if primaryIdentifier is not None and primaryIdentifier['type'] == 'uuid':
            return Work.getByUUID(session, primaryIdentifier['identifier'])

        existingWorkID = Identifier.getByIdentifier(Work, session, identifiers)
        if existingWorkID:
            return session.query(Work).get(existingWorkID)
        else:
            existingInstanceID = Identifier.getByIdentifier(Instance, session, identifiers)
            if existingInstanceID:
                return session.query(Instance).get(existingInstanceID).work

    @classmethod
    def getByUUID(cls, session, recUUID):
        """Query the database for a work by UUID. Returns only one record or
        errors. (If duplicate UUIDs exist, a serious error has occured)"""
        qUUID = uuid.UUID(recUUID)
        try:
            existing = session.query(Work)\
                .filter(Work.uuid == qUUID)\
                .one()
        except NoResultFound:
            logger.error('No matching UUID {} found!'.format(recUUID))
            raise DBError('work', 'Original UUID {} not found, check error logs'.format(
                recUUID
            ))
        return existing

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
            self.subjects.add(
                Subject.updateOrInsert(session, subject)
            )


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
