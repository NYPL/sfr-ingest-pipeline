import os

from lib.outputManager import OutputManager

LOOKUP_IDENTIFIERS = [
    'oclc',   # OCLC Number
    'isbn',   # ISBN (10 or 13)
    'issn',   # ISSN
    'upc',    # UPC (Probably unused)
    'lccn',   # LCCN
    'swid',   # OCLC Work Identifier
    'stdnbr'  # Sandard Number (unclear)
]


def queryWork(work, workUUID):
    """This takes a work record that has not been queried for enhanced data
    and begins that process. It extracts one of two things from the work record
    to allow for this lookup.
    If it contains an identifier in the list defined
    in LOOKUP_IDENTIFIERS, it will pass that identifier to the Kinesis stream.
    If not it will pass the author and title of the work.
    It will also pass the UUID of the database record, which will be used to
    match the returned data with the existing record."""

    lookupIDs = getIdentifiers(work.identifiers)

    if len(lookupIDs) == 0:
        # If no identifiers are in the work record, lookup via title/author
        authors = getAuthors(work.agent_works)
        print(work.title, authors)
        OutputManager.putKinesis({
            'type': 'authorTitle',
            'uuid': workUUID,
            'fields': {
                'title': work.title,
                'authors': authors
            }
        }, os.environ['CLASSIFY_STREAM'])
    else:
        # Otherwise, pass all valid identifiers to the Classify service
        for idType, ids in lookupIDs.items():
            for iden in ids:
                OutputManager.putKinesis({
                    'type': 'identifier',
                    'uuid': workUUID,
                    'fields': {
                        'idType': idType,
                        'identifier': iden.value
                    }
                }, os.environ['CLASSIFY_STREAM'])


def getIdentifiers(identifiers):
    """Checks for the existence of identifiers that can be used with the OCLC
    Classify API. If none are found, will return an empty dict"""

    lookupIDs = {}

    for identifier in identifiers:
        for source in LOOKUP_IDENTIFIERS:
            try:
                if len(getattr(identifier, source)) > 0:
                    lookupIDs[source] = []
                    sourceList = getattr(identifier, source)
                    for iden in sourceList:
                        lookupIDs[source].append(iden)
            except AttributeError:
                pass

    return lookupIDs


def getAuthors(agentWorks):
    """Concatenate all authors into a comma-delimited string"""

    agents = []

    for rel in agentWorks:
        if rel.role == 'author':
            agents.append(rel.agent.name)

    return ', '.join(agents)
