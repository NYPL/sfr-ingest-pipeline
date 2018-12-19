import requests
import os
from lxml import etree

from helpers.errorHelpers import OCLCError
from helpers.logHelpers import createLog

logger = createLog('classify_read')

NAMESPACE = {
    None: 'http://classify.oclc.org'
}

LOOKUP_IDENTIFIERS = [
    'oclc', # OCLC Number
    'isbn', # ISBN (10 or 13)
    'issn', # ISSN
    'upc',  # UPC (Probably unused)
    'lccn', # LCCN
    'swid', # OCLC Work Identifier
    'stdnbr'# Sandard Number (unclear)
]

def classifyRecord(source, data, recID):
    queryURL = formatURL(source, data, recID)
    logger.info('Fetching data for url: {}'.format(queryURL))

    # Load Query Response from OCLC Classify
    logger.debug('Making Classify request')
    rawData = queryClassify(queryURL)

    # Parse response, and if it is a Multi-Work response, parse further
    logger.debug('Parsing Classify Response')
    xmlData, sourceData = parseClassify(rawData, data)

    return xmlData, sourceData


def parseClassify(rawXML, sourceData):
    try:
        parseXML = etree.fromstring(rawXML.encode('utf-8'))
    except etree.XMLSyntaxError as err:
        logger.error('Classify returned invalid XML')
        logger.debug(err)
        raise OCLCError('Received invalid XML from OCLC service')

    # Check for the type of response we recieved
    # 2: Single-Work Response
    # 4: Multi-Work Response
    # 102: No Results found for query
    # Other: Raise Error
    responseXML = parseXML.find('.//response', namespaces=NAMESPACE)
    responseCode = int(responseXML.get('code'))

    storedWorks = []
    if responseCode == 102:
        return None, sourceData
    elif responseCode == 2:
        logger.debug('Got Single Work, parsing work and edition data')
        work = parseXML.find('.//work', namespaces=NAMESPACE)
        if len(list(filter(lambda x: x['identifier'] == work.text, sourceData['identifiers']))) < 1:
            sourceData['identifiers'].append({
                'type': 'oclc',
                'identifier': work.text,
                'weight': 0.9
            })
        storedWorks.append(parseXML)
    elif responseCode == 4:
        logger.debug('Got Multiwork response, iterate through works to get details')
        works = parseXML.findall('.//work', namespaces=NAMESPACE)

        for work in works:
            oclcID = work.get('wi')

            # Skip records that we've alread parsed
            if len(list(filter(lambda x: x['identifier'] == oclcID, sourceData['identifiers']))) > 0:
                continue

            sourceData['identifiers'].append({
                'type': 'oclc',
                'identifier': oclcID,
                'weight': 0.9
            })

            workData, sourceData = classifyRecord('oclc', sourceData, oclcID)
            storedWorks.extend(workData)
    else:
        raise OCLCError('Recieved unexpected response {} from Classify'.format(responseCode))

    return storedWorks, sourceData

def queryClassify(queryURL):

    classifyResp = requests.get(queryURL)
    if classifyResp.status_code != 200:
        logger.error('OCLC Classify Request failed')
        raise OCLCError('Failed to reach OCLC Classify Service')

    classifyBody = classifyResp.text
    return classifyBody


def formatURL(source, record, recID):
    title = None
    author = None
    lookupID = None
    recType = None
    logger.debug('Generating URL for Record')
    authors = list(a['name'] for a in filter(lambda x: 'author' in x['roles'], record['agents']))

    author = None
    if len(authors) > 0:
        author = ", ".join(authors)

    title = record['title']

    for identifier in record['identifiers']:
        if identifier['type'] in LOOKUP_IDENTIFIERS:
            lookupID = identifier['identifier']
            recType = identifier['type']

    return generateClassifyURL(lookupID, recType, title, author)


def generateClassifyURL(recID=None, recType=None, title=None, author=None):
    classifyRoot = "http://classify.oclc.org/classify2/Classify?"
    if recID is not None:
        classifySearch = "{}{}={}".format(classifyRoot, recType, recID)
    else:
        titleParam = 'title={}'.format(title)
        if author is not None:
            authorParam = '&author={}'.format(author)

        classifySearch = "{}{}{}".format(classifyRoot, titleParam, authorParam)

    return '{}&wskey={}&summary=false'.format(classifySearch, os.environ['OCLC_KEY'])
