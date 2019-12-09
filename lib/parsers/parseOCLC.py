import copyreg
from datetime import datetime
from io import BytesIO
from lxml import etree
import requests
from multiprocessing import Process, Queue

from helpers.logHelpers import createLog
from lib.dataModel import WorkRecord, InstanceRecord, Agent, Identifier, Subject, Measurement

logger = createLog('classify_parse')

NAMESPACE = {
    None: 'http://classify.oclc.org'
}

MEASUREMENT_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

MARC_FIELDS = {
    '050': 'lcc',
    '082': 'ddc'
}


def readFromClassify(workXML, workUUID):
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
            work.text
        ))

    authors = workXML.findall('.//author', namespaces=NAMESPACE)
    authorList = list(map(parseAuthor, authors))

    editions = workXML.findall('.//edition', namespaces=NAMESPACE)
    editionList = loadEditions(editions, workUUID)

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


def loadEditions(editions, uuid):
    processes = []
    cores = 4
    logger.info('Processing {} editions'.format(len(editions)))
    edQueue = Queue()
    outQueue = Queue()

    for ed in editions:
        edQueue.put(ed)

    for i in range(cores):
        edQueue.put('DONE')  # Put end message for each process
        proc = Process(target=parseQueue, args=(edQueue, outQueue))
        processes.append(proc)
        proc.start()

    for proc in processes:
        proc.join()

    outEds = []
    while outQueue.empty() is False:
        outEds.append(outQueue.get())

    return outEds


def etreePickler(tree):
    return etreeUnPickler, (etree.tostring(tree),)


def etreeUnPickler(data):
    return etree.parse(BytesIO(data))


copyreg.pickle(etree._Element, etreePickler, etreeUnPickler)


def parseQueue(edQueue, outQueue):
    while True:
        element = edQueue.get()
        if element == 'DONE':
            break

        outQueue.put(parseEdition(element))


def parseEdition(element):
    """Parse an edition into a Instance record"""
    edition = element.getroot()
    oclcIdentifier = edition.get('oclc')
    oclcNo = Identifier(
        'oclc',
        oclcIdentifier,
        1
    )

    identifiers = [
        oclcNo
    ]

    fullEditionRec = None
    try:
        logger.info('Querying OCLC lookup for {}'.format(oclcIdentifier))
        oclcRoot = 'https://dev-platform.nypl.org/api/v0.1/research-now/v3/utils/oclc-catalog'
        oclcQuery = '{}?identifier={}&type={}'.format(
            oclcRoot, oclcIdentifier, 'oclc'
        )
        edResp = requests.get(oclcQuery)
        if edResp.status_code == 200:
            logger.debug('Found matching OCLC record')
            fullEditionRec = edResp.json()
    except Exception as err:
        logger.debug('Error received when querying OCLC catalog')
        logger.error(err)

    classifications = edition.findall('.//class', namespaces=NAMESPACE)
    classificationList = list(map(parseClassification, classifications))
    identifiers.extend(classificationList)

    holdings = Measurement(
        'holdings',
        edition.get('holdings'),
        1,
        MEASUREMENT_TIME,
        oclcIdentifier
    )

    digHoldings = Measurement(
        'digitalHoldings',
        edition.get('eholdings'),
        1,
        MEASUREMENT_TIME,
        oclcIdentifier
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

    if fullEditionRec is not None:
        outEdition = fullEditionRec
        outEdition['title'] = editionDict['title']
        outEdition['identifiers'].extend(editionDict['identifiers']) 
        outEdition['measurements'].extend(editionDict['measurements'])
        outEdition['language'] = list(set(
           [outEdition['language'], editionDict['language']]
        ))
    else:
        outEdition = editionDict

    print(outEdition)
    return InstanceRecord.createFromDict(**outEdition)


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
