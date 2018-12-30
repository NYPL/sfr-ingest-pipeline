from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Unicode,
)
from sqlalchemy.orm import relationship

from model.core import Base, Core


#
# A simple table to hold alternate titles
#
class AltTitle(Core, Base):

    __tablename__ = 'alt_titles'
    id = Column(Integer, primary_key=True)
    title = Column(Unicode, index=True)
    work_id = Column(Integer, ForeignKey('works.id'))

    work = relationship('Work', back_populates='alt_titles')

    def __repr__(self):
        return '<AltTitle(title={}, work={})>'.format(self.title, self.work)

    @classmethod
    def insertOrSkip(cls, session, title, model, recordID):
        existing = session.query(cls)\
            .join(model)\
            .filter(cls.title == title)\
            .filter(model.id == recordID)\
            .one_or_none()
        if existing is not None:
            return False
        return cls(title=title)
