from sqlalchemy import (
    Column,
    Integer,
)
from sqlalchemy.orm import relationship

from .base import Base


class OLIDS(Base):
    olid = Column(Integer, nullable=False, unique=True)
    identifiers = relationship('Identifiers', backref='olid')
