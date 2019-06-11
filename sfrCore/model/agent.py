import re
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

from .core import Base, Core
from .link import AGENT_LINKS, Link
from .date import AGENT_DATES, DateField

from ..helpers import createLog, DataError

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
    sort_name = Column(Unicode)
    lcnaf = Column(String(25), index=True)
    viaf = Column(String(25), index=True)
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

    VIAF_API = 'https://dev-platform.nypl.org/api/v0.1/research-now/viaf-lookup?queryName='  # noqa: E501

    RELS = ['aliases', 'roles', 'link', 'dates']

    def __init__(self, session=None):
        self.session = session

    def __repr__(self):
        return '<Agent(name={}, sort_name={}, lcnaf={}, viaf={})>'.format(
            self.name,
            self.sort_name,
            self.lcnaf,
            self.viaf
        )
    
    def __dir__(self):
        return ['name', 'sort_name', 'lcnaf', 'viaf', 'biography']

    def createTmpRelations(self, agentData):
        for relType in Agent.RELS:
            tmpRel = 'tmp_{}'.format(relType)
            if getattr(self, tmpRel, None): continue
            tmpData = agentData.pop(relType, []) if agentData.get(relType, None) else []
            setattr(self, tmpRel, tmpData)
    
    def removeTmpRelations(self):
        """Removes temporary attributes that were used to hold related objects.
        """
        for rel in Agent.RELS: delattr(self, 'tmp_{}'.format(rel))

    @classmethod
    def updateOrInsert(cls, session, agentData):
        """Evaluates whether a matching record exists and either updates that
        agent record or creates a new one"""

        agentRec, roles = Agent.createAgent(session, agentData)
        existingAgentID = agentRec.lookup()

        if existingAgentID is not None:
            existingAgent = session.query(cls).get(existingAgentID)
            roles = existingAgent.update(session, agentData)
            return existingAgent, roles


        return agentRec, roles

    @classmethod
    def createAgent(cls, session, agentData):
        agentRec = Agent(session=session)
        agentRec.createTmpRelations(agentData)
        
        for dateType in ['birth_date', 'death_date']:
            agentRec.addLifespan(dateType, agentData.pop(dateType, None))

        agentRec.insertData(agentData)
        agentRec.cleanName()
        # parse agent roles for duplicates
        roles = list(set([ r.lower() for r in agentRec.tmp_roles ]))

        if len(agentRec.name.strip()) < 1:
            raise DataError('Received empty string for agent name')

        agentRec.removeTmpRelations()

        return agentRec, roles

    def update(self, session, agentData):
        """Updates an existing agent record"""
        
        self.createTmpRelations(agentData)
        for field, value in agentData.items():
            if(
                value is not None and
                value.strip() != '' and
                value != getattr(self, field)
            ):
                setattr(self, field, value)        

        self.cleanName()

        if self.tmp_aliases is not None:
            aliasRecs = {
                Alias.insertOrSkip(session, a, Agent, self.id)
                for a in self.tmp_aliases
            }
            for alias in list(filter(None, aliasRecs)):
                self.aliases.add(alias)

        if type(self.tmp_link) is dict: self.tmp_link = [self.tmp_link]

        if type(self.tmp_link) is list:
            for linkItem in self.tmp_link:
                self.links.add(
                    Link.updateOrInsert(
                        session,
                        linkItem,
                        Agent,
                        self.id
                    )
                )

        for date in self.tmp_dates:
            self.dates.add(
                DateField.updateOrInsert(session, date, Agent, self.id)
            )
        
        roles = self.tmp_roles
        self.removeTmpRelations()

        return roles

    def insertData(self, agentData):
        """Inserts a new agent record"""
        logger.debug('Inserting new agent: {}'.format(self.name))
        
        for field, value in agentData.items(): setattr(self, field, value)

        if self.sort_name is None:
            # TODO Order sort_name in last, first order always
            self.sort_name = self.name

        for alias in list(map(lambda x: Alias(alias=x), self.tmp_aliases)):
            self.aliases.add(alias)

        if type(self.tmp_link) is dict:
            self.tmp_link = [self.tmp_link]

        if type(self.tmp_link) is list:
            self.links = { Link(**l) for l in self.tmp_link }

        self.dates = { 
            DateField.insert(d) 
            for d in { d['date_type']:d for d in self.tmp_dates }.values()
        }

    def lookup(self):
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
        
        if self.viaf is not None or self.lcnaf is not None:
            agentRec = self.authorityQuery()
        else:
            agentRec = self.findViafQuery()
        
        if agentRec is None:
            agentRec = self.findJaroWinklerQuery()

        return agentRec

    def addLifespan(self, dateType, lifespanDate):
        if lifespanDate:
            self.tmp_dates.append({
                'display_date': lifespanDate,
                'date_range': lifespanDate,
                'date_type': dateType
            })

    def findJaroWinklerQuery(self):
        logger.debug('Matching agent based off jaro_winkler score')
        
        escapedName = self.name.replace('\'', '\'\'')
        try:
            jaroWinklerQ = text(
                "jarowinkler({}, '{}') > {}".format('name', escapedName, 0.95)
            )
            return self.session.query(Agent.id)\
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

    def findViafQuery(self):
        viafResp = requests.get('{}{}'.format(Agent.VIAF_API, self.name))
        responseJSON = viafResp.json()
        logger.debug(responseJSON)
        if 'viaf' in responseJSON:
            if responseJSON['name'] != self.name:
                self.aliases.add(Alias(alias=self.name))
                self.name = responseJSON.get('name', '')
                self.cleanName()
            self.viaf = responseJSON.get('viaf', None)
            self.lcnaf = responseJSON.get('lcnaf', None)
            return self.authorityQuery()
        
        return None
        
    def authorityQuery(self):
        logger.debug('Matching agent on VIAF/LCNAF')
        orFilters = []
        if self.viaf: orFilters.append(Agent.viaf == self.viaf)
        if self.lcnaf: orFilters.append(Agent.lcnaf == self.lcnaf)
        authQuery = self.session.query(Agent.id).filter(or_(*orFilters))
        try:
            return authQuery.one_or_none()
        except MultipleResultsFound:
            logger.warning(
                'Multiple matches for {}/{}. returning First'.format(
                    self.viaf, self.lcnaf
                )
            )
            return authQuery.first()

    def cleanName(self):
        """Parse agent name to normalize and remove/assign roles/dates"""
        tmpName = self.name
        # Escape single quotes for postgres and other string cleaning methods
        tmpName = tmpName.strip(' ,;:')\
                .replace('\'', '\'\'')\
                .replace('\r', ' ')\
                .replace('\n', ' ')\
                .replace('\'\'', '\'')\
                .strip()
            
        if re.match(r'^\[.+\]$', tmpName):
            tmpName = tmpName.strip('[]')

        # Parse and remove lifespan dates from the author name string
        lifeGroup = re.search(r'([0-9]{4})\-(?:([0-9]{4})|)', tmpName)
        if lifeGroup is not None:
            if getattr(self, 'tmp_dates', None) is None: setattr(self, 'tmp_dates', [])
            tmpName = tmpName.replace(lifeGroup.group(0), '')
            try:
                birthDate = lifeGroup.group(1)
                if birthDate is not None:
                    self.tmp_dates.append({
                        'display_date': birthDate,
                        'date_range': birthDate,
                        'date_type': 'birth_date'
                    })
            except IndexError:
                pass
            
            try:
                deathDate = lifeGroup.group(2)
                if deathDate is not None:
                    self.tmp_dates.append({
                        'display_date': deathDate,
                        'date_range': deathDate,
                        'date_type': 'death_date'
                    })
            except IndexError:
                pass

        # Parse and remove roles from the author name string
        roleGroup = re.search(r'\[([a-zA-Z; ]+)\]', tmpName)
        if roleGroup is not None:
            if getattr(self, 'tmp_roles', None) is None: setattr(self, 'tmp_roles', [])
            tmpName = tmpName.replace(roleGroup.group(0), '')
            tmpRoles = roleGroup.group(1).split(';')
            cleanRoles = [r.lower().strip() for r in tmpRoles]
            self.tmp_roles.extend(cleanRoles)
        
        # Strip punctuation from end of name string
        self.name = tmpName.rstrip('.,;:|[]" ')
        self.sort_name = self.name


class Alias(Core, Base):
    """Alternate, or variant names for an agent."""
    __tablename__ = 'aliases'
    id = Column(Integer, primary_key=True)
    alias = Column(Unicode, index=True)
    agent_id = Column(Integer, ForeignKey('agents.id'), index=True)

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
