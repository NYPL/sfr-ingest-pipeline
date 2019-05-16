from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    Integer,
    Unicode,
)
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from .core import Base, Core

WORK_ALTS = Table(
    'work_alt_titles',
    Base.metadata,
    Column('work_id', Integer, ForeignKey('works.id')),
    Column('title_id', Integer, ForeignKey('alt_titles.id'))
)

INSTANCE_ALTS = Table(
    'instance_alt_titles',
    Base.metadata,
    Column('instance_id', Integer, ForeignKey('instances.id')),
    Column('title_id', Integer, ForeignKey('alt_titles.id'))
)

class AltTitle(Core, Base):
    """Contains alternate titles for works"""
    __tablename__ = 'alt_titles'
    id = Column(Integer, primary_key=True)
    title = Column(Unicode, index=True)

    work = relationship(
        'Work',
        secondary=WORK_ALTS,
        back_populates='alt_titles'
    )
    instance = relationship(
        'Instance',
        secondary=INSTANCE_ALTS,
        back_populates='alt_titles'
    )

    def __repr__(self):
        return '<AltTitle(title={}, work={})>'.format(self.title, self.work)

    @classmethod
    def insertOrSkip(cls, session, title, model, recordID):
        """Queries database for alt title associated with current work. If
        found, returns false. Otherwise it creates a new alt title entry and
        returns it"""

        try:
            session.query(cls)\
                .join(model.__tablename__[:-1])\
                .filter(cls.title == title)\
                .filter(model.id == recordID)\
                .one()
            return None
        except NoResultFound:
            return cls(title=title)

