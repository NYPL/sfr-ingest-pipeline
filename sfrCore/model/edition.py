from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Unicode,
    func
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import DATERANGE

from .core import Base, Core
from .work import Work
from .instance import Instance

from ..helpers import createLog

logger = createLog('editions')


class Edition(Core, Base):
    __tablename__ = 'editions'
    id = Column(Integer, primary_key=True)
    publication_place = Column(Unicode)
    publication_date = Column(DATERANGE)
    edition = Column(Unicode)
    edition_statement = Column(Unicode)
    volume = Column(Unicode)
    table_of_contents = Column(Unicode)
    extent = Column(Unicode)
    summary = Column(Unicode)

    work_id = Column(Integer, ForeignKey('works.id'))

    work = relationship(
        'Work',
        backref=backref('editions', collection_class=set)
    )

    def __init__(self, pubDate=None, pubPlace=None, work=None):
        self.publication_date = pubDate
        self.publication_place = pubPlace
        self.work = work

    def __repr__(self):
        return '<Edition(place={}, date={}, publisher={})>'.format(
            self.publication_place,
            self.publication_date,
            self.loadPublishers()
        )

    @staticmethod
    def createEdition(metadata, work, instances):
        newEdition = Edition(
            pubDate=metadata.pop('pubDate', None),
            pubPlace=metadata.pop('pubPlace', None),
            work=work
        )

        newEdition.addMetadata(metadata)
        newEdition.addInstances(instances)

        return newEdition

    def addMetadata(self, metadata):
        for column, value in metadata.items():
            setattr(self, column, value)

    def addInstances(self, instances):
        self.instances = set(instances)

    @staticmethod
    def getExistingEdition(session, work, instances):
        return session.query(Edition.id)\
            .join(Work, Instance)\
            .filter(Work.id == work.id)\
            .filter(Instance.id.in_(i.id for i in instances))\
            .group_by(Edition.id)\
            .having(func.count(Edition.instances) == len(instances))\
            .one_or_none()

    def loadPublishers(self):
        publishers = set()
        for instance in self.instances:
            for agent in instance.instance_agents:
                if agent.role == 'publisher':
                    publishers.add(agent.agent.name)

        return '; '.join(list(publishers))
