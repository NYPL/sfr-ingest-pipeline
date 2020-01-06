import copyreg
from datetime import datetime
from io import BytesIO
from lxml import etree
import math
import requests
from multiprocessing import Process, Pipe
from multiprocessing.connection import wait
from urllib.parse import quote_plus

from helpers.logHelpers import createLog
from helpers.errorHelpers import DataError
from lib.dataModel import WorkRecord, InstanceRecord, Agent, Identifier, Subject, Measurement
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


def readFromClassify(workXML, workUUID):
    """Parse Classify XML document into a object that complies with the
    SFR data model. Accepts a single XML document and returns a WorkRecord."""
    logger.debug('Parsing Returned Work')

    work = workXML.find('.//work', namespaces=NAMESPACE)

    oclcTitle = work.get('title')
    oclcNo = Identifier('oclc', work.text, 1)
    owiNo = Identifier('owi', work.get('owi'), 1)

    if OutputManager.checkRecentQueries('lookup/{}/{}'.format('owi', work.get('owi'))) is True:
        raise DataError('Work {} with OWI {} already classified'.format(
            workUUID, work.get('owi')
        ))

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
    editionList = loadEditions(editions)

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

    instanceCount = int(work.get('editions', 0))

    return WorkRecord.createFromDict(**workDict), instanceCount, work.text


def extractAndAppendEditions(work, classifyXML):
    editions = classifyXML.findall('.//edition', namespaces=NAMESPACE)
    work.instances.extend(loadEditions(editions))


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


def loadEditions(editions):
    processes = []
    outPipes = []
    cores = 4
    logger.info('Processing {} editions'.format(len(editions)))

    chunkSize = math.ceil(len(editions) / cores)

    for i in range(cores):
        start = i * chunkSize
        end = start + chunkSize
        logger.info('Processing chunk {} to {}'.format(start, end))

        pConn, cConn = Pipe(duplex=False)
        proc = Process(target=parseChunk, args=(editions[start:end], cConn))
        processes.append(proc)
        outPipes.append(pConn)
        proc.start()
        cConn.close()

    outEds = []
    while outPipes:
        for p in wait(outPipes):
            try:
                ed = p.recv()
                if ed == 'DONE':
                    outPipes.remove(p)
                else:
                    outEds.append(ed)
            except EOFError:
                outPipes.remove(p)

    for proc in processes:
        proc.join()

    return outEds


def etreePickler(tree):
    return etreeUnPickler, (etree.tostring(tree),)


def etreeUnPickler(data):
    return etree.parse(BytesIO(data))


copyreg.pickle(etree._Element, etreePickler, etreeUnPickler)


def parseChunk(editions, cConn):
    for edition in editions:
        try:
            editionData = parseEdition(edition)
            cConn.send(editionData)
        except Exception as err:
            logger.error('Unable to parse edition, skipping')
            logger.debug(err)

    cConn.send('DONE')
    cConn.close()


def parseEdition(edition):
    """Parse an edition into a Instance record"""
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
    if OutputManager.checkRecentQueries('lookup/{}/{}'.format('oclc', oclcIdentifier)) is False:
        try:
            logger.info('Querying OCLC lookup for {}'.format(oclcIdentifier))
            oclcRoot = 'https://dev-platform.nypl.org/api/v0.1/research-now/v3/utils/oclc-catalog'
            oclcQuery = '{}?identifier={}&type={}'.format(
                oclcRoot, oclcIdentifier, 'oclc'
            )
            edResp = requests.get(oclcQuery, timeout=10)
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

    if authorDict['viaf'] is None or authorDict['lcnaf'] is None:
        logger.info('Querying VIAF for {}'.format(authorDict['name']))
        viafResp = requests.get('{}{}'.format(
        'https://dev-platform.nypl.org/api/v0.1/research-now/viaf-lookup?queryName=',
            quote_plus(authorDict['name'])
        ))
        responseJSON = viafResp.json()
        logger.debug(responseJSON)
        if 'viaf' in responseJSON:
            logger.debug('Found VIAF {} for agent'.format(responseJSON.get('viaf', None)))
            if responseJSON['name'] != authorDict['name']:
                authorDict['aliases'] = [authorDict['name']]
                authorDict['name'] = responseJSON.get('name', '')
            authorDict['viaf'] = responseJSON.get('viaf', None)
            authorDict['lcnaf'] = responseJSON.get('lcnaf', None)

    return Agent.createFromDict(**authorDict)
