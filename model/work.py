import uuid
import json
from sqlalchemy import (
    Column,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Unicode,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy

from model.core import Base, Core
from model.subject import SUBJECT_WORKS
from model.identifiers import (
    WORK_IDENTIFIERS,
    Identifier,
    Gutenberg,
    OCLC,
    OWI
)
from model.altTitle import AltTitle
from model.rawData import RawData
from model.measurement import WORK_MEASUREMENTS, Measurement
from model.link import WORK_LINKS
from model.instance import Instance
from model.agent import Agent
from model.subject import Subject

from helpers.logHelpers import createLog

logger = createLog('workModel')


#
# The root-level SFR record of Work corresponds to the FRBR and BIBFRAME
# concepts at the same level.
#
class Work(Core, Base):

    __tablename__ = 'works'
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False)
    title = Column(Unicode, index=True)
    sort_title = Column(Unicode, index=True)
    sub_title = Column(Unicode, index=True)
    language = Column(String(2), index=True)
    issued = Column(Date)
    published = Column(Date)
    license = Column(String(50))
    rights_statement = Column(Unicode)
    medium = Column(Unicode)
    series = Column(Unicode)
    series_position = Column(Integer)

    #
    # Relationships
    #

    alt_titles = relationship('AltTitle', back_populates='work')
    subjects = relationship('Subject', secondary=SUBJECT_WORKS, back_populates='work')
    instances = relationship('Instance', back_populates='work')
    agents = association_proxy('agent_works', 'agent')
    measurements = relationship('Measurement', secondary=WORK_MEASUREMENTS, back_populates='work')
    identifiers = relationship('Identifier', secondary=WORK_IDENTIFIERS, back_populates='work')
    links = relationship('Link', secondary=WORK_LINKS, back_populates='works')
    import_json = relationship('RawData', back_populates='work')

    def __repr__(self):
        return "<Work(title={})>".format(self.title)

    @classmethod
    def updateOrInsert(cls, session, workData):
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
            json=storeJson
        )

        return 'insert', newWork

    @classmethod
    def update(cls, session, existing, work, **kwargs):

        logger.debug('Updating existing work record {}'.format(existing.id))

        instances = kwargs.get('instances', [])
        identifiers = kwargs.get('identifiers', [])
        agents = kwargs.get('agents', [])
        altTitles = kwargs.get('alt_titles', [])
        subjects = kwargs.get('subjects', [])
        measurements = kwargs.get('measurements', [])
        links = kwargs.get('links', [])
        storeJson = kwargs.get('json')
        for field, value in work.items():
            if (
                value is not None and
                value.strip() != '' and
                field != 'title'
            ):
                setField = getattr(existing, field)
                setField = value

        newTitle = work.get('title')
        # The "canonical title" should be set to the record with the most holdings
        if newTitle.lower() != existing.title.lower():
            newHoldings = list(filter(lambda x: x['quantity'] == 'holdings', measurements))[0]
            oldHoldings = list(filter(lambda x: x.quantity == 'holdings', existing.measurements))

            for holding in oldHoldings:
                if newHoldings.value > holding.value:
                    existing.title = newTitle
                    break
            else:
                existing.altTitle.append(AltTitle(title=newTitle))


        for instance in instances:
            instanceRec = Instance.updateOrInsert(session, instance)
            if instanceRec is not None:
                existing.instances.append(instanceRec)

        for iden in identifiers:
            status, idenRec = Identifier.returnOrInsert(session, iden, Work, existing.id)
            if status == 'new':
                existing.identifiers.append(idenRec)

        for agent in agents:
            agentRec, roles = Agent.updateOrInsert(session, agent)
            if roles is None:
                roles = ['author']
            for role in roles:
                if AgentWorks.roleExists(session, agentRec, role, Work, existing.id) is None:
                    AgentWorks(
                        agent=agentRec,
                        work=existing,
                        role=role
                    )

        for altTitle in list(filter(lambda x: AltTitle.insertOrSkip(session, x, Work, existing.id), altTitles)):
            existing.altTitles.append(AltTitle(title=altTitle))

        for subject in subjects:
            op, subjectRec = Subject.updateOrInsert(session, subject)
            relExists = Work.lookupSubjectRel(session, subjectRec, existing.id)
            if relExists is None:
                existing.subjects.append(subjectRec)

        for measurement in measurements:
            # TODO Do we want to merge measurements in some instances?
            # Leaving as is for now
            measurementRec = Measurement.insert(measurement)
            existing.measurements.append(measurementRec)

        return existing



    @classmethod
    def insert(cls, session, workData, **kwargs):

        logger.info('Inserting new work record')

        # TODO Remove prepositions, etc from the start of the sort title
        workData['sort_title'] = workData.get('sort_title', workData['title'])
        print(workData)
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

        jsonRec = RawData(data=storeJson)
        work.import_json.append(jsonRec)

        for instance in instances:
            instanceRec = Instance.updateOrInsert(session, instance)
            work.instances.append(instanceRec)

        for iden in identifiers:
            idenRec = Identifier.insert(iden)
            work.identifiers.append(idenRec)

        for agent in agents:
            agentRec, roles = Agent.updateOrInsert(session, agent)
            for role in roles:
                AgentWorks(
                    agent=agentRec,
                    work=work,
                    role=role
                )

        for altTitle in altTitles:
            work.altTitles.append(AltTitle(title=altTitle))

        for subject in subjects:
            op, subjectRec = Subject.updateOrInsert(session, subject)
            work.subjects.append(subjectRec)

        for measurement in measurements:
            measurementRec = Measurement.insert(measurement)
            work.measurements.append(measurementRec)

        return work


    @classmethod
    def lookupWork(cls, session, identifiers, primaryIdentifier=None):
        if primaryIdentifier is not None and primaryIdentifier['type'] == 'uuid':
            return Work.getByUUID(session, primaryIdentifier['identifier'])

        return Identifier.getByIdentifier(Work, session, identifiers)


    @classmethod
    def getByUUID(cls, session, recUUID):
        qUUID = uuid.UUID(recUUID)
        existing = session.query(Work)\
            .filter(Work.uuid == qUUID)\
            .one()
        return existing

    @classmethod
    def lookupSubjectRel(cls, session, subject, workID):
        return session.query(cls)\
            .join("subjects")\
            .filter(Subject.subject == subject.subject)\
            .filter(cls.id == workID)\
            .one_or_none()


class AgentWorks(Core, Base):

    __tablename__ = 'agent_works'
    work_id = Column(Integer, ForeignKey('works.id'), primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), primary_key=True)
    role = Column(String(64))

    work = relationship(Work, backref=backref('agent_works', cascade='all, delete-orphan'))
    agent = relationship('Agent')

    def __repr__(self):
        return '<AgentWorks(work={}, agent={}, role={})>'.format(self.work_id, self.agent_id, self.role)

    @classmethod
    def roleExists(cls, session, agent, role, model, recordID):
        return session.query(cls)\
            .join(Agent)\
            .join(model)\
            .filter(Agent.id == agent.id)\
            .filter(model.id == recordID)\
            .filter(cls.role == role)\
            .one_or_none()
