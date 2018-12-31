from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Unicode,
)
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from model.core import Base, Core


class AltTitle(Core, Base):
    """Contains alternate titles for works"""
    __tablename__ = 'alt_titles'
    id = Column(Integer, primary_key=True)
    title = Column(Unicode, index=True)
    work_id = Column(Integer, ForeignKey('works.id'))

    work = relationship('Work', back_populates='alt_titles')

    def __repr__(self):
        return '<AltTitle(title={}, work={})>'.format(self.title, self.work)

    @classmethod
    def insertOrSkip(cls, session, title, model, recordID):
        """Queries database for alt title associated with current work. If
        found, returns false. Otherwise it creates a new alt title entry and
        returns it"""

        try:
            session.query(cls)\
                .join(model)\
                .filter(cls.title == title)\
                .filter(model.id == recordID)\
                .one()
        except NoResultFound:
            return cls(title=title)

        return False
