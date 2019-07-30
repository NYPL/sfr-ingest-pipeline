import unicodedata

from sqlalchemy import Column, DateTime, Unicode
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from ..helpers import createLog

Base = declarative_base()


def validate_unicode(value):
    if value is None:
        return value
    if isinstance(value, bytes):
        value = value.decode('utf-8')
    assert isinstance(value, str)
    return unicodedata.normalize('NFC', value)


validators = {
    Unicode: validate_unicode
}


# Add unicode validator to normalize all strings to NFC style, not NFD
@listens_for(Base, 'attribute_instrument')
def configure_unicode_listener(dbClass, key, inst):
    if not hasattr(inst.property, 'columns'):
        return

    @listens_for(inst, 'set', retval=True)
    def setVal(instance, val, oldVal, initiator):
        validator = validators.get(inst.property.columns[0].type.__class__)
        if validator:
            return validator(val)

        return val


logger = createLog('core_model')


class Core(object):
    """A mixin for other SQLAlchemy ORM classes. Includes a date_craeted and
    date_updated field for all database tables."""
    date_created = Column(
        DateTime,
        default=datetime.utcnow()
    )

    date_modified = Column(
        DateTime,
        default=datetime.utcnow(),
        onupdate=datetime.utcnow()
    )
