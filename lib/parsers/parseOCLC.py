import os
from lxml import etree
from itertools import repeat
from datetime import datetime

from helpers.errorHelpers import OCLCError
from helpers.logHelpers import createLog
from lib.dataModel import WorkRecord, InstanceRecord, Format, Agent, Identifier, Link, Subject, Measurement
from lib.outputManager import OutputManager

logger = createLog('classify_parse')

NAMESPACE = {
    None: 'http://classify.oclc.org'
}

MEASUREMENT_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

MARC_FIELDS = {
    '050': 'lcc',
    '082': 'ddc'
}


def readFromClassify(workXML):
    """Parse Classify XML document into a object that complies with the
    SFR data model. Accepts a single XML document and returns a WorkRecord."""
    logger.debug('Parsing Returned Work')

    work = workXML.find('.//work', namespaces=NAMESPACE)

    oclcTitle = work.get('title')
    oclcNo = Identifier('oclc', work.text, 1)
    owiNo = Identifier('owi', work.get('owi'), 1)

    measurements = []
    for measure in ['editions', 'holdings', 'eholdings']:
        measurements.append(Measurement(
            measure,
            work.get(measure),
            1,
            MEASUREMENT_TIME,
            oclcNo
        ))

    authors = workXML.findall('.//author', namespaces=NAMESPACE)
    authorList = list(map(parseAuthor, authors))

    editions = workXML.findall('.//edition', namespaces=NAMESPACE)
    editionList = list(map(parseEdition, editions))

    headings = workXML.findall('.//heading', namespaces=NAMESPACE)
    headingList = list(map(parseHeading, headings))

    workDict = {
        'title': oclcTitle,
        'agents': authorList,
        'instances': editionList,
        'subjects': headingList,
        'identifiers': [
            oclcNo,
            owiNo
        ],
        'measurements': measurements
    }

    return WorkRecord.createFromDict(**workDict)


def parseHeading(heading):
    """Parse a subject heading into a data model object"""
    headingDict = {
        'subject': heading.text,
        'uri': heading.get('ident'),
        'authority': heading.get('src')
    }

    subject = Subject.createFromDict(**headingDict)
    subject.addMeasurement(
        quantity='holdings',
        value=heading.get('heldby'),
        weight=1,
        taken_at=MEASUREMENT_TIME
    )

    return subject

def parseEdition(edition):
    """Parse an edition into a Instance record"""
    oclcNo = Identifier(
        'oclc',
        edition.get('oclc'),
        1
    )

    identifiers = [
        oclcNo
    ]

    # Put OCLC# into Kinesis stream for reading by OCLC Lookup service
    if OutputManager.checkRecentQueries('lookup/{}/{}'.format(oclcNo.type, oclcNo.identifier)) is False:
        OutputManager.putQueue({
            'type': oclcNo.type,
            'identifier': oclcNo.identifier
        })

    classifications = edition.findall('.//class', namespaces=NAMESPACE)
    classificationList = list(map(parseClassification, classifications))
    identifiers.extend(classificationList)

    holdings = Measurement(
        'holdings',
        edition.get('holdings'),
        1,
        MEASUREMENT_TIME,
        oclcNo
    )

    digHoldings = Measurement(
        'digitalHoldings',
        edition.get('eholdings'),
        1,
        MEASUREMENT_TIME,
        oclcNo
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
    """Parse a classification into an identifier for the work record."""
    tag = classification.get('tag')
    subjectType = MARC_FIELDS[tag]

    classDict = {
        'type': subjectType,
        'identifier': classification.get('sfa'),
        'weight': 1
    }

    return Identifier.createFromDict(**classDict)

def parseAuthor(author):
    """Parse a supplied author into an agent record."""
    authorDict = {
        'name': author.text,
        'viaf': author.get('viaf'),
        'lcnaf': author.get('lc')
    }

    return Agent.createFromDict(**authorDict)
