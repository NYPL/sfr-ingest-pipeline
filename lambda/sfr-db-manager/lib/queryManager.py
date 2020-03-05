from sfrCore import Work
from sfrCore.model.identifiers import (
    OCLC,
    OWI,
    LCCN,
    ISBN,
    ISSN,
    Identifier,
    WORK_IDENTIFIERS
)

from lib.outputManager import OutputManager
from helpers.logHelpers import createLog

# Other Possible Identifiers
# upc
# stdnbr
LOOKUP_IDENTIFIERS = [
    'oclc',   # OCLC Number
    'isbn',   # ISBN (10 or 13)
    'issn',   # ISSN
    'swid',   # OCLC Work Identifier
]

IDENTIFIER_TYPES = {
        'oclc': OCLC,
        'swid': OWI,
        'isbn': ISBN,
        'issn': ISSN,
    }

logger = createLog('query_constructor')


def queryWork(session, work, workUUID):
    """This takes a work record that has not been queried for enhanced data
    and begins that process. It extracts one of two things from the work record
    to allow for this lookup.
    If it contains an identifier in the list defined
    in LOOKUP_IDENTIFIERS, it will pass that identifier to the Kinesis stream.
    If not it will pass the author and title of the work.
    It will also pass the UUID of the database record, which will be used to
    match the returned data with the existing record."""

    lookupIDs = getIdentifiers(session, work)
    classifyQueries = []

    if len(lookupIDs) == 0:
        # If no identifiers are in the work record, lookup via title/author
        authors = getAuthors(work.agent_works)
        workTitleFields = {
            'title': work.title,
            'authors': authors
        }
        classifyQueries.append(
            createClassifyQuery(workTitleFields, 'authorTitle', workUUID)
        )
    else:
        # Otherwise, pass all valid identifiers to the Classify service
        for idType, ids in lookupIDs.items():
            for iden in ids:
                idenFields = {
                    'idType': idType,
                    'identifier': iden
                }
                classifyQueries.append(
                    createClassifyQuery(idenFields, 'identifier', workUUID)
                )
    return classifyQueries


def getIdentifiers(session, work):
    """Checks for the existence of identifiers that can be used with the OCLC
    Classify API. If none are found, will return an empty dict"""

    lookupIDs = {}
    for source in LOOKUP_IDENTIFIERS:
        typeIDs = session.query(IDENTIFIER_TYPES[source].value)\
            .join(Identifier, WORK_IDENTIFIERS, Work)\
            .filter(Work.id == work.id)\
            .all()
        if len(typeIDs) < 1:
            continue
        lookupIDs[source] = [i[0] for i in typeIDs]

    return lookupIDs


def getAuthors(agentWorks):
    """Concatenate all authors into a comma-delimited string"""

    agents = []

    for rel in agentWorks:
        if rel.role == 'author':
            agents.append(rel.agent.name)

    return ', '.join(agents)


def createClassifyQuery(classifyQuery, queryType, uuid):
    queryStr = [value for key, value in classifyQuery.items()]
    if OutputManager.checkRecentQueries(
        '{}'.format('/'.join(queryStr))
    ) is False:
        return {
            'type': queryType,
            'uuid': uuid,
            'fields': classifyQuery
        }
    else:
        logger.info('{} was recently queried, can skip Classify'.format(
            '/'.join(queryStr)
        ))
