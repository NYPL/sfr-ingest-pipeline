from lxml import etree
from itertools import repeat
from Levenshtein import distance, jaro_winkler
from datetime import datetime

from helpers.errorHelpers import OCLCError
from helpers.logHelpers import createLog
from lib.dataModel import WorkRecord, InstanceRecord, Format, Agent, Identifier, Link, Subject, Measurement

logger = createLog('classify_parse')

NAMESPACE = {
    None: 'http://classify.oclc.org'
}

MEASUREMENT_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

MARC_FIELDS = {
    '050': 'lcc',
    '082': 'ddc'
}


def readFromClassify(classifyRecs):
    # Extract relevant data from returned works
    logger.debug('Parsing Returned Works')
    extractedData = extractFromXML(classifyRecs)

    combinedData = combineData(extractedData)

    return combinedData


def extractFromXML(xmlData):
    return list(map(parseWork, xmlData))


def parseWork(workXML):
    namespaces = {
        None: 'http://classify.oclc.org'
    }
    work = workXML.find('.//work', namespaces=NAMESPACE)

    oclcTitle = work.get('title')

    measurements = []
    for measure in ['editions', 'holdings', 'eholdings']:
        measurements.append(Measurement(
            measure,
            work.get(measure),
            1,
            MEASUREMENT_TIME
        ))
    oclcNo = Identifier('oclc', work.text, 1)
    owiNo = Identifier('owi', work.get('owi'), 1)

    authors = workXML.findall('.//author', namespaces=NAMESPACE)
    authorList = list(map(parseAuthor, authors))

    editions = workXML.findall('.//edition', namespaces=NAMESPACE)
    editionList = list(map(parseEdition, editions))

    headings = workXML.findall('.//heading', namespaces=NAMESPACE)
    headingList = list(map(parseHeading, headings))

    workDict = {
        'oclcTitle': oclcTitle,
        'authors': authorList,
        'editions': editionList,
        'headings': headingList,
        'identifiers': [
            oclcNo,
            owiNo
        ],
        'measurements': measurements
    }

    return WorkRecord.createFromDict(**workDict)


def parseHeading(heading):

    return {
        'text': heading.text,
        'id': heading.get('ident'),
        'source': heading.get('src'),
        'holdings': heading.get('heldby')
    }

def parseEdition(edition):

    oclcNo = Identifier(
        'oclc',
        edition.get('oclc'),
        1
    )

    identifiers = [
        oclcNo
    ]

    classifications = edition.findall('.//class', namespaces=NAMESPACE)
    classificationList = list(map(parseClassification, classifications))
    identifiers.extend(classificationList)

    holdings = Measurement(
        'holdings',
        edition.get('holdings'),
        1,
        MEASUREMENT_TIME
    )

    digHoldings = Measurement(
        'digitalHoldings',
        edition.get('eholdings'),
        1,
        MEASUREMENT_TIME
    )

    language = edition.get('language')
    editionTitle = edition.get('title')

    editionDict = {
        'title': editionTitle,
        'language': language,
        'identifiers': identifiers,
        'measurements': [
            holdings,
            digHoldings
        ]
    }

    return InstanceRecord.createFromDict(**editionDict)

def parseClassification(classification):

    tag = classification.get('tag')
    subjectType = MARC_FIELDS[tag]

    classDict = {
        'type': subjectType,
        'value': classification.get('sfa'),
        'identifier': None,
        'weight': 1
    }

    return Identifier.createFromDict(**classDict)

def parseAuthor(author):

    authorDict = {
        'name': author.text,
        'viaf': author.get('viaf'),
        'lcnaf': author.get('lc')
    }

    return Agent.createFromDict(**authorDict)

def combineData(extractedData):
    workTitle = None
    workTitles = []
    editionCount = 0
    holdings = 0
    digHoldings = 0
    authors = []
    editions = []
    headings = []
    measurements = []

    for work in extractedData:

        if int(Measurement.getValueForMeasurement(work['measurements'], 'editions')) > editionCount:
            workTitle = work['oclcTitle']

        workTitles.append(work['oclcTitle'])
        holdings += int(Measurement.getValueForMeasurement(work['measurements'], 'holdings'))
        digHoldings += int(Measurement.getValueForMeasurement(work['measurements'], 'eholdings'))
        editionCount += int(Measurement.getValueForMeasurement(work['measurements'], 'editions'))

        authors.extend(list(filter(None, map(authorCheck, work['authors'], repeat(authors)))))

        editions.extend(list(filter(None, map(editionCheck, work['editions'], repeat(editions)))))

        headings.extend(list(filter(None, map(headingCheck, work['headings'], repeat(headings)))))

    for measure in [('editions', editionCount), ('holdings', holdings), ('eholdings', digHoldings)]:
        measurements.append(Measurement(
            measure[0],
            measure[1],
            1,
            MEASUREMENT_TIME
        ))

    mergedData = {
        "workTitle": workTitle,
        "altTitles": workTitles,
        "authors": authors,
        "editions": editions,
        "subjects": headings,
        "measurements": measurements
    }

    return WorkRecord.createFromDict(**mergedData)

def headingCheck(heading, existing):

    if len(existing) < 1:
        return heading

    if len(list(filter(lambda x: x['id'] == heading['id'], existing))) > 0:
        return False

    return heading

def editionCheck(edition, existing):

    if len(existing) < 1:
        return edition

    if len(list(filter(lambda x: x['identifiers'][0]['identifier'] == edition['identifiers'][0]['identifier'], existing))) > 0:
        return False

    return edition

def authorCheck(author, existing):

    if len(existing) < 1:
        return author

    for exist in existing:
        if jaro_winkler(author['name'].lower(), exist['name'].lower()) > 0.8:
            return False

    return author
