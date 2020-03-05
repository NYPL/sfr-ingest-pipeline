from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String
)

from .base import Base


class Identifiers(Base):
    id_type = Column(String, nullable=False)
    identifier = Column(String, nullable=False)
    olid_id = Column(Integer, ForeignKey('olids.id'))
