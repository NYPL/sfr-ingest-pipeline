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

    def __repr__(self):
        return '<Work(title={})>'.format(self.title)

    def importSubjects(self, session, subjects):
        for subject in subjects:
            op, subjectRec = Subject.updateOrInsert(session, subject)
            relExists = Work.lookupSubjectRel(session, subjectRec, self.id)
            if relExists is None:
                self.subjects.append(subjectRec)

    @classmethod
    def updateOrInsert(cls, session, workData):
        """Search for an existing work, if found update it, if not create
        a new work record"""
        logger.info('Ingesting record, checking if update or insert')
        storeJson = json.dumps(workData)

        primaryIdentifier = workData.pop('primary_identifier', None)
        instances = workData.pop('instances', None)
        agents = workData.pop('agents', None)
        altTitles = workData.pop('alt_titles', None)
        subjects = workData.pop('subjects', None)
        identifiers = workData.pop('identifiers', None)
        measurements = workData.pop('measurements', None)
        links = workData.pop('links', None)
        dates = workData.pop('dates', None)
        rights = workData.pop('rights', [])
        language = workData.pop('language', [])

        existing = cls.lookupWork(session, identifiers, primaryIdentifier)
        if existing is not None:
            updated = Work.update(
                session,
                existing,
                workData,
                instances=instances,
                identifiers=identifiers,
                agents=agents,
                altTitles=altTitles,
                subjects=subjects,
                measurements=measurements,
                links=links,
                dates=dates,
                rights=rights,
                language=language,
                json=storeJson
            )
            return 'update', updated

        # Insert a new work
        newWork = cls.insert(
            session,
            workData,
            instances=instances,
            identifiers=identifiers,
            agents=agents,
            altTitles=altTitles,
            subjects=subjects,
            measurements=measurements,
            links=links,
            dates=dates,
            rights=rights,
            language=language,
            json=storeJson
        )

        return 'insert', newWork

    @classmethod
    def update(cls, session, existing, work, **kwargs):
        """Update an existing work record"""
        logger.debug('Updating existing work record {}'.format(existing.id))

        instances = kwargs.get('instances', [])
        identifiers = kwargs.get('identifiers', [])
        agents = kwargs.get('agents', [])
        altTitles = kwargs.get('alt_titles', [])
        subjects = kwargs.get('subjects', [])
        measurements = kwargs.get('measurements', [])
        links = kwargs.get('links', [])
        storeJson = kwargs.get('json')
        dates = kwargs.get('dates', [])
        rights = kwargs.get('rights', [])
        language = kwargs.get('language', [])

        jsonRec = RawData(data=storeJson)
        existing.import_json.append(jsonRec)

        for field, value in work.items():
            if (
                value is not None
                and value.strip() != ''
                and field != 'title'
            ):
                setattr(existing, field, value)

        newTitle = work.get('title')
        # The "canonical title" should be set to the record with the most holdings
        if newTitle.lower() != existing.title.lower():
            newHoldings = list(filter(lambda x: x['quantity'] == 'holdings', measurements))
            if len(newHoldings) < 1:
                newHoldings = {'value': 0}
            else:
                newHoldings = newHoldings[0]

            oldHoldings = Measurement.getMeasurements(
                session,
                'holdings',
                Work,
                existing.id
            )

            for holding in oldHoldings:
                try:
                    if float(newHoldings['value']) > float(holding.value):
                        existing.title = newTitle
                        break
                except TypeError:
                    pass
            else:
                newAlt = AltTitle.insertOrSkip(
                    session,
                    newTitle,
                    Work,
                    existing.id
                )
                if newAlt is not None:
                    existing.alt_titles.append(newAlt)

        for instance in instances:
            instanceRec, op = Instance.updateOrInsert(
                session,
                instance, 
                work=existing
            )
            if op == 'inserted':
                existing.instances.append(instanceRec)

        for iden in identifiers:
            try:
                status, idenRec = Identifier.returnOrInsert(
                    session,
                    iden
                )
                if status == 'new':
                    existing.identifiers.append(idenRec)
                else:
                    if Identifier.getIdentiferRelationship(
                        session,
                        idenRec,
                        Work,
                        existing.id
                    ) is None:
                        existing.identifiers.append(idenRec)
            except DataError as err:
                logger.warning('Received invalid identifier')
                logger.debug(err)

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

        for altTitle in list(filter(lambda x: AltTitle.insertOrSkip(session, x, Work, existing.id), altTitles)):
            existing.alt_titles.append(altTitle)

        for subject in subjects:
            op, subjectRec = Subject.updateOrInsert(session, subject)
            relExists = Work.lookupSubjectRel(session, subjectRec, existing.id)
            if relExists is None:
                existing.subjects.append(subjectRec)

        for measurement in measurements:
            op, measurementRec = Measurement.updateOrInsert(
                session,
                measurement,
                Work,
                existing.id
            )
            if op == 'insert':
                existing.measurements.append(measurementRec)

        for link in links:
            updateLink = Link.updateOrInsert(session, link, Work, existing.id)
            if updateLink is not None:
                existing.links.append(updateLink)

        for date in dates:
            updateDate = DateField.updateOrInsert(session, date, Work, existing.id)
            if updateDate is not None:
                existing.dates.append(updateDate)
        
        #for rightsStmt in rights:
        #    updateRights = Rights.updateOrInsert(
        #        session,
        #        rightsStmt,
        #        Work,
        #        existing.id
        #    )
        #    if updateRights is not None:
        #        existing.rights.append(updateRights)
        
        if isinstance(language, str) or language is None:
            language = [language]

        for lang in language:
            try:
                newLang = Language.updateOrInsert(session, lang)
                langRel = Language.lookupRelLang(session, newLang, Work, existing)
                if langRel is None:
                    existing.language.append(newLang)
            except DataError:
                logger.warning('Unable to parse language {}'.format(lang))


        return existing

    @classmethod
    def insert(cls, session, workData, **kwargs):
        """Insert a new work record"""
        logger.info('Inserting new work record')

        # TODO Remove prepositions, etc from the start of the sort title
        workData['sort_title'] = workData.get('sort_title', workData['title'])
        
        work = cls(**workData)
        #
        # === IMPORTANT ===
        # This inserts a uuid value for the db row
        # This might want to be a namespaced UUID in the future, but for now
        # it will be a random v4 value
        #
        work.uuid = uuid.uuid4()

        instances = kwargs.get('instances', [])
        identifiers = kwargs.get('identifiers', [])
        agents = kwargs.get('agents', [])
        altTitles = kwargs.get('alt_titles', [])
        subjects = kwargs.get('subjects', [])
        measurements = kwargs.get('measurements', [])
        links = kwargs.get('links', [])
        storeJson = kwargs.get('json')
        dates = kwargs.get('dates', [])
        rights = kwargs.get('rights', [])
        language = kwargs.get('language', [])

        jsonRec = RawData(data=storeJson)
        work.import_json.append(jsonRec)
        
        for instance in instances:
            instanceRec, op = Instance.updateOrInsert(session, instance)
            work.instances.append(instanceRec)

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

        # Quick conversion to set to eliminate duplicate alternate titles
        for altTitle in list(set(altTitles)):
            work.alt_titles.append(AltTitle(title=altTitle))

        for subject in subjects:
            op, subjectRec = Subject.updateOrInsert(session, subject)
            work.subjects.append(subjectRec)

        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            work.measurements.append(measurementRec)

        for link in links:
            newLink = Link(**link)
            work.links.append(newLink)

        for date in dates:
            newDate = DateField.insert(date)
            work.dates.append(newDate)
        
        #for rightsStmt in rights:
        #    rightsDates = rightsStmt.pop('dates', [])
        #    newRights = Rights.insert(rightsStmt, dates=rightsDates)
        #    work.rights.append(newRights)
        
        if isinstance(language, str) or language is None:
            language = [language]
        
        for lang in language:
            try:
                newLang = Language.updateOrInsert(session, lang)
                work.language.append(newLang)
            except DataError:
                logger.debug('Unable to parse language {}'.format(lang))
                continue
            
        return work

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
