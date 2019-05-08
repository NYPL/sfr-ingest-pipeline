import re
import os
import requests
from dateutil.parser import parse
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Unicode,
    or_
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from model.core import Base, Core
from model.link import AGENT_LINKS, Link
from model.date import AGENT_DATES, DateField

from helpers.logHelpers import createLog
from helpers.errorHelpers import DataError

logger = createLog('agentModel')


class Agent(Core, Base):
    """An agent records an individual, organization, or family that is
    associated with the production of a FRBR entity (work, instance or item).
    Agents may be associated with one or more of these entities and can have
    multiple aliases and links (generally to Wikipedia or other reference
    sources).

    Agents are uniquely identifier by the VIAF and LCNAF authorities, though
    not all agents will have this data. Attempts to merge agents lacking
    authority control is made at the time of import."""

    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, index=True)
    sort_name = Column(Unicode, index=True)
    lcnaf = Column(String(25))
    viaf = Column(String(25))
    biography = Column(Unicode)

    aliases = relationship(
        'Alias',
        back_populates='agent',
        collection_class=set
    )
    links = relationship(
        'Link',
        secondary=AGENT_LINKS,
        back_populates='agents',
        collection_class=set
    )

    VIAF_API = os.environ['VIAF_API']

    def __repr__(self):
        return '<Agent(name={}, sort_name={}, lcnaf={}, viaf={})>'.format(
            self.name,
            self.sort_name,
            self.lcnaf,
            self.viaf
        )

    @classmethod
    def updateOrInsert(cls, session, agent):
        """Evaluates whether a matching record exists and either updates that
        agent record or creates a new one"""
        aliases = agent.pop('aliases', [])
        roles = agent.pop('roles', [])
        link = agent.pop('link', [])
        dates = agent.pop('dates', [])

        agent.pop('birth_date', None)
        agent.pop('death_date', None)

        if roles is None: roles = []
        if dates is None: dates = []
        if aliases is None: aliases = []

        Agent._cleanName(agent, roles, dates)
        roles = list(set([ r.lower() for r in roles ]))
        if len(agent['name'].strip()) < 1:
            raise DataError('Received empty string for agent name')
        
        existingAgentID = Agent.lookupAgent(
            session,
            agent,
            aliases,
            roles,
            dates
        )
        if existingAgentID is not None:
            existingAgent = session.query(cls).get(existingAgentID)
            Agent.update(
                session,
                existingAgent,
                agent,
                aliases=aliases,
                link=link,
                dates=dates
            )
            return existingAgent, roles

        newAgent = Agent.insert(
            agent,
            aliases=aliases,
            link=link,
            dates=dates
        )

        return newAgent, roles

    @classmethod
    def update(cls, session, existing, agent, **kwargs):
        """Updates an existing agent record"""
        aliases = kwargs.get('aliases', [])
        link = kwargs.get('link', [])
        dates = kwargs.get('dates', [])

        for field, value in agent.items():
            if(
                value is not None
                and value.strip() != ''
                and value != getattr(existing, field)
            ):
                setattr(existing, field, value)        

        if aliases is not None:
            aliasRecs = {
                Alias.insertOrSkip(session, a, Agent, existing.id)
                for a in aliases
            }
            for alias in list(filter(None, aliasRecs)):
                existing.aliases.add(alias)

        if type(link) is dict:
            link = [link]

        if type(link) is list:
            for linkItem in link:
                existing.links.add(
                    Link.updateOrInsert(session, linkItem, Agent, existing.id)
                )

        for date in dates:
            existing.dates.add(
                DateField.updateOrInsert(session, date, Agent, existing.id)
            )

    @classmethod
    def insert(cls, agentData, **kwargs):
        """Inserts a new agent record"""
        logger.debug('Inserting new agent: {}'.format(agentData['name']))
        agent = Agent(**agentData)

        if agent.sort_name is None:
            # TODO Order sort_name in last, first order always
            agent.sort_name = agent.name

        aliases = kwargs.get('aliases', [])
        link = kwargs.get('link', [])
        dates = kwargs.get('dates', [])

        if aliases is not None:
            for alias in list(map(lambda x: Alias(alias=x), aliases)):
                agent.aliases.add(alias)

        if type(link) is dict:
            link = [link]

        if type(link) is list:
            agent.links = { Link(**l) for l in link }

        uniqueDates = { d['date_type']:d for d in dates }.values()
        agent.dates = { DateField.insert(d) for d in uniqueDates }

        return agent

    @classmethod
    def lookupAgent(cls, session, agent, aliases, roles, dates):
        """Attempts to retrieve a matching record from the database for the
        current agent. It does so in the following order of preference:
        1) A VIAF or LCNAF identifier attached to the current record.
        2) A VIAF or LCNAF that can be found by querying the OCLC VIAF API.
        3) A fuzzy text match using the jaro_winkler algorithm.
        
        Arguments:
            session {Session} -- A postgreSQL connection instance
            agent {dict} -- A dict describing an agent received from an outside
            source
            aliases {list} -- A list of alternate agent names
        
        Returns:
            [Agent] -- An ORM Agent model from postgreSQL. If not found returns
            None.
        """
        
        if agent['viaf'] is not None or agent['lcnaf'] is not None:
            agentRec = Agent._authorityQuery(session, agent)
        elif len(agent['name']) > 4:
            agentRec = Agent._findViafQuery(
                session,
                agent,
                aliases,
                roles,
                dates
            )
        else:
            agentRec = None
        if agentRec is None:
            agentRec = Agent._findJaroWinklerQuery(session, agent)

        return agentRec

    @classmethod
    def _findJaroWinklerQuery(cls, session, agent):
        logger.debug('Matching agent based off jaro_winkler score')
        
        escapedName = agent['name'].replace('\'', '\'\'')
        try:
            jaroWinklerQ = text(
                "jarowinkler({}, '{}') > {}".format('name', escapedName, 0.95)
            )
            return session.query(cls.id)\
                .filter(jaroWinklerQ)\
                .one()
            
        except MultipleResultsFound:
            logger.info(
                'Name/information is too generic to create individual record'
            )
            pass
        except NoResultFound:
            pass
        
        return None

    @classmethod
    def _findViafQuery(cls, session, agent, aliases, roles, dates):
        viafResp = requests.get('{}{}'.format(cls.VIAF_API, agent['name']))
        responseJSON = viafResp.json()
        logger.debug(responseJSON)
        if 'viaf' in responseJSON:
            if responseJSON['name'] != agent['name']:
                aliases.append(agent['name'])
                agent['name'] = responseJSON.get('name', '')
                Agent._cleanName(agent, roles, dates)
            agent['viaf'] = responseJSON.get('viaf', None)
            agent['lcnaf'] = responseJSON.get('lcnaf', None)
            return Agent._authorityQuery(session, responseJSON)
        
        return None
        
    @classmethod
    def _authorityQuery(cls, session, agent):
        logger.debug('Matching agent on VIAF/LCNAF')
        orFilters = []
        if agent.get('viaf', None):
            orFilters.append(cls.viaf == agent.get('viaf', None))
        if agent.get('lcnaf', None):
            orFilters.append(cls.viaf == agent.get('lcnaf', None))
        authQuery = session.query(cls.id).filter(or_(*orFilters))
        try:
            return authQuery.one_or_none()
        except MultipleResultsFound as err:
            logger.warning(
                'Multiple matches for {}/{}. returning First'.format(
                    agent.get('viaf', None), agent.get('lcnaf', None)
                )
            )
            return authQuery.first()

    @classmethod
    def _cleanName(cls, agent, roles, dates):
        """Parse agent name to normalize and remove/assign roles/dates"""
        # Escape single quotes for postgres
        tmpName = agent['name']
        tmpName = tmpName.replace('\'', '\'\'')
        if re.match(r'^\[.+\]$', tmpName):
            tmpName = tmpName.strip('[]')

        # Parse and remove lifespan dates from the author name string
        lifeGroup = re.search(r'([0-9]{4})\-(?:([0-9]{4})|)', tmpName)
        if lifeGroup is not None:
            tmpName = tmpName.replace(lifeGroup.group(0), '')
            try:
                birthDate = lifeGroup.group(1)
                if birthDate is not None:
                    dates.append({
                        'display_date': birthDate,
                        'date_range': birthDate,
                        'date_type': 'birth_date'
                    })
            except IndexError:
                pass
            
            try:
                deathDate = lifeGroup.group(2)
                if deathDate is not None:
                    dates.append({
                        'display_date': deathDate,
                        'date_range': deathDate,
                        'date_type': 'death_date'
                    })
            except IndexError:
                pass

        # Parse and remove roles from the author name string
        roleGroup = re.search(r'\[([a-zA-Z; ]+)\]', tmpName)
        if roleGroup is not None:
            tmpName = tmpName.replace(roleGroup.group(0), '')
            tmpRoles = roleGroup.group(1).split(';')
            cleanRoles = [r.lower().strip() for r in tmpRoles]
            roles.extend(cleanRoles)
        
        # Strip punctuation from end of name string
        agent['name'] = tmpName.strip('.,;:|[]" ')
        agent['sort_name'] = agent['name']


class Alias(Core, Base):
    """Alternate, or variant names for an agent."""
    __tablename__ = 'aliases'
    id = Column(Integer, primary_key=True)
    alias = Column(Unicode, index=True)
    agent_id = Column(Integer, ForeignKey('agents.id'))

    agent = relationship('Agent', back_populates='aliases')

    def __repr__(self):
        return '<Alias(alias={}, agent={})>'.format(self.alias, self.agent)

    @classmethod
    def insertOrSkip(cls, session, alias, model, recordID):
        """Queries database for alias associated with current agent. If alias
        exists, we can skip this, no modification is needed. If it is not
        found, a new alias is created."""

        alias = alias.replace('\'', '\'\'')

        try:
            session.query(cls)\
                .join(model)\
                .filter(Alias.alias == alias)\
                .filter(model.id == recordID)\
                .one()
        except NoResultFound:
            return Alias(alias=alias)
