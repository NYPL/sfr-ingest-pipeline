import requests
import os
from lxml import etree

from helpers.errorHelpers import OCLCError
from helpers.logHelpers import createLog

from lib.kinesisWrite import KinesisOutput

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

def classifyRecord(searchType, searchFields, workUUID):
    # TODO Check to be sure that we have not queried this URL recently
    # Probably within the last 24 hours
    queryURL = formatURL(searchType, searchFields)
    logger.info('Fetching data for url: {}'.format(queryURL))

    # Load Query Response from OCLC Classify
    logger.debug('Making Classify request')
    rawData = queryClassify(queryURL)

    # Parse response, and if it is a Multi-Work response, parse further
    logger.debug('Parsing Classify Response')
    return parseClassify(rawData, workUUID)


def parseClassify(rawXML, workUUID):
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

    if responseCode == 102:
        logger.info('Did not find any information for this query')
        return None
    elif responseCode == 2:
        logger.debug('Got Single Work, parsing work and edition data')
        work = parseXML.find('.//work', namespaces=NAMESPACE)
        return parseXML
    elif responseCode == 4:
        logger.debug('Got Multiwork response, iterate through works to get details')
        works = parseXML.findall('.//work', namespaces=NAMESPACE)

        for work in works:
            oclcID = work.get('wi')

            KinesisOutput.putRecord({
                'type': 'identifier',
                'uuid': workUUID,
                'fields': {
                    'idType': 'oclc',
                    'identifier': oclcID
                }
            }, os.environ['CLASSIFY_STREAM'])

            storedWorks.extend(workData)

        return None
    else:
        raise OCLCError('Recieved unexpected response {} from Classify'.format(responseCode))

        return None

def queryClassify(queryURL):

    classifyResp = requests.get(queryURL)
    if classifyResp.status_code != 200:
        logger.error('OCLC Classify Request failed')
        raise OCLCError('Failed to reach OCLC Classify Service')

    classifyBody = classifyResp.text
    return classifyBody


def formatURL(searchType, searchFields):

    if searchType == 'authorTitle':
        return generateClassifyURL(None, None, searchFields['title'], searchFields['authors'])
    elif searchType == 'identifier':
        return generateClassifyURL(searchFields['identifier'], searchFields['idType'], None, None)



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
