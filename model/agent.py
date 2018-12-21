import uuid
from dateutil.parser import parse
from sqlalchemy import (
    Column,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Unicode,
    DateTime,
    Table,
    or_
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import text

from model.core import Base, Core
from model.link import AGENT_LINKS, Link

from helpers.logHelpers import createLog

logger = createLog('agentModel')

class Agent(Core, Base):

    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, index=True)
    sort_name = Column(Unicode, index=True)
    lcnaf = Column(String(25))
    viaf = Column(String(25))
    biography = Column(Unicode)
    birth_date = Column(Date, default=None)
    death_date = Column(Date, default=None)

    aliases = relationship('Alias', back_populates='agent')
    links = relationship('Link', secondary=AGENT_LINKS, back_populates='agents')


    def __repr__(self):
        return '<Agent(name={}, sort_name={}, lcnaf={}, viaf={})>'.format(self.name, self.sort_name, self.lcnaf, self.viaf)


    @classmethod
    def updateOrInsert(cls, session, agent):
        aliases = agent.pop('aliases', [])
        roles = agent.pop('roles', [])
        link = agent.pop('link', [])

        existingAgent = Agent.lookupAgent(session, agent)

        if existingAgent is not None:
            updated = Agent.update(
                session,
                existingAgent,
                agent,
                aliases=aliases,
                link=link
            )
            return updated, roles

        newAgent = Agent.insert(
            agent,
            aliases=aliases,
            link=link
        )
        return newAgent, roles


    @classmethod
    def update(cls, session, existing, agent, **kwargs):

        aliases = kwargs.get('aliases', [])
        link = kwargs.get('link', [])

        for field, value in agent.items():
            if(value is not None and value.strip() != ''):
                setField = getattr(existing, field)
                setField = value

        if aliases is not None:
            for alias in list(filter(lambda x: AltTitle.insertOrSkip(session, x, Agent, existing.id), aliases)):
                existing.aliases.append(alias)

        if link is not None:
            updateLink = Link.updateOrInsert(session, link, Agent, existing.id)
            if updateLink is not None:
                existing.links.append(newLink)

        return existing


    @classmethod
    def insert(cls, agentData, **kwargs):
        logger.debug('Inserting new agent record: {}'.format(agentData['name']))
        agent = Agent(**agentData)

        if agent.sort_name is None:
            # TODO Order sort_name in last, first order always
            agent.sort_name = agent.name

        for dateField in ['birth_date', 'death_date']:
            agentField = getattr(agent, dateField)
            try:
                # TODO Improve checking to see if this is a valid date value?
                agentField = parse(agentField)
            except ValueError:
                logger.info('Got invalid date object {}'.format(agentField))
                agentField = None
            except TypeError:
                logger.debug('Got an empty date field')
                continue
            setattr(agent, dateField, agentField)

        aliases = kwargs.get('aliases', [])
        roles = kwargs.get('roles', ['author'])
        link = kwargs.get('link', [])

        if aliases is not None:
            for alias in list(map(lambda x: Alias(alias=x), aliases)):
                agent.aliases.append(alias)

        if link is not None:
            newLink = Link(**link)
            agent.links.append(newLink)

        return agent


    @classmethod
    def lookupAgent(cls, session, agent):
        if agent['viaf'] is not None and agent['lcnaf'] is not None:
            logger.debug('Matching agent on VIAF/LCNAF')
            agnts = session.query(Agent)\
                .filter(or_(Agent.viaf == agent['viaf'], Agent.lcnaf == agent['lcnaf']))\
                .all()
            if len(agnts) == 1:
                return agnts[0]
            elif len(agnts) > 1:
                logger.error('Found multiple matching agents, should only be one record per identifier')
                raise

        logger.debug('Matching agent based off jaro_winkler score')
        jaroWinklerQ = text(
            "SELECT * FROM {} WHERE jarowinkler({}, '{}') > {}".format('agents', 'name', agent['name'], 0.95)
        )
        agnts = session.execute(jaroWinklerQ).fetchall()
        if len(agnts) == 1:
            return agnts[0]
        elif len(agnts) > 1:
            logger.info('Name/information is too generic to create individual record')
            pass

        return None

class Alias(Core, Base):

    __tablename__  = 'aliases'
    id = Column(Integer, primary_key=True)
    alias = Column(Unicode, index=True)
    agent_id = Column(Integer, ForeignKey('agents.id'))

    agent = relationship('Agent', back_populates='aliases')

    def __repr__(self):
        return '<Alias(alias={}, agent={})>'.format(self.alias, self.agent)

    @classmethod
    def insertOrSkip(cls, session, alias, model, recordID):
        existing = session.query(cls)\
            .join(model)\
            .filter(Alias.alias == alias)\
            .filter(model.id == recordID)\
            .one_or_none()
        if existing is not None:
            return False
        return cls(alias=alias)
