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
    lookupIDs = getIdentifiers(work.identifiers)
    if len(lookupIDs) == 0:
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
        for idType, ids in lookupIDs.items():
            for iden in ids:
                OutputManager.putKinesis({
                    'type': 'identifier',
                    'uuid': workUUID,
                    'fields': {
                        'idType': idType,
                        'identifier': iden
                    }
                }, os.environ['CLASSIFY_STREAM'])


def getIdentifiers(identifiers):
    lookupIDs = {}
    for identifier in identifiers:
        for source in LOOKUP_IDENTIFIERS:
            try:
                if len(getattr(identifier, source)) > 0:
                    lookupIDs[source] = []
                    sourceList = getattr(identifier, source)
                    for iden in sourceList:
                        lookupIDs.append(iden)
            except AttributeError:
                pass

    return lookupIDs


def getAuthors(agentWorks):
    agents = []
    for rel in agentWorks:
        if rel.role == 'author':
            agents.append(rel.agent.name)

    return ', '.join(agents)
