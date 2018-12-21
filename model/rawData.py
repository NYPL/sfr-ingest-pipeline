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
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from model.core import Base, Core
#
# A that holds version-controlled raw copies of the import JSON blocks
#
class RawData(Core, Base):

    __tablename__ = 'import_json'
    id = Column(Integer, primary_key=True)
    data = Column(JSON)
    work_id = Column(Integer, ForeignKey('works.id'))

    work = relationship('Work', back_populates='import_json')

    def __repr__(self):
        return '<ImportJSON(id={}, work={})>'.format(self.id, self.work)
