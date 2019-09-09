from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from .core import Base, Core


class RawData(Core, Base):
    """This table holds the raw JSON objects received through the import
    process. Each successive JSON block is stored, timestamped and associated
    with the relevant work record"""
    __tablename__ = 'import_json'
    id = Column(Integer, primary_key=True)
    data = Column(JSON)
    work_id = Column(Integer, ForeignKey('works.id'), index=True)

    work = relationship('Work', back_populates='import_json')

    def __repr__(self):
        return '<ImportJSON(id={}, work={})>'.format(self.id, self.work)

    def __init__(self, data):
        self.data = data