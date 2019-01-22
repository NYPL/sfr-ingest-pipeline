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
    """Generates a query for the OCLC Classify service and returns the raw
    XML response recieved from that service. This method takes 3 arguments:
    - searchType: identifier|authorTitle
    - searchFields: identifier+idType|authors+title
    - uuid: UUID of the parent work record"""
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
    """Parses results received from Classify. Response is based of the code
    recieved from the service, generically it will response with the XML of a
    work record or None if it recieves a different response code.

    If a multi-response is recieved, those identifiers are put back into the
    processing stream, this will recurse until a single work record is
    found."""
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
        raise OCLCError('No work records found in OCLC Classify Service')
    elif responseCode == 2:
        logger.debug('Got Single Work, parsing work and edition data')
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

        raise OCLCError('Received Multi-Work response from Classify, returned records to input stream')
    else:
        raise OCLCError('Recieved unexpected response {} from Classify'.format(responseCode))


def queryClassify(queryURL):
    """Execute a request against the OCLC Classify service"""
    classifyResp = requests.get(queryURL)
    if classifyResp.status_code != 200:
        logger.error('OCLC Classify Request failed')
        raise OCLCError('Failed to reach OCLC Classify Service')

    classifyBody = classifyResp.text
    return classifyBody


def formatURL(searchType, searchFields):
    """Create a URL query for the Classify service depending on the type.
    authorTitle search will create a query based on the title and author(s) of
    a work. identifier will create a query based on one of a standardized set
    of identifiers."""
    if searchType == 'authorTitle':
        searchTitle = searchFields['title'].replace('\r', ' ').replace('\n', ' ')
        return generateClassifyURL(None, None, searchFields['title'], searchFields['authors'])
    elif searchType == 'identifier':
        return generateClassifyURL(searchFields['identifier'], searchFields['idType'], None, None)



def generateClassifyURL(recID=None, recType=None, title=None, author=None):
    """Append the parameters recieved from formatURL to the Classify service
    base URL and return a formatted URL"""
    classifyRoot = "http://classify.oclc.org/classify2/Classify?"
    if recID is not None:
        classifySearch = "{}{}={}".format(classifyRoot, recType, recID)
    else:
        titleParam = 'title={}'.format(title)
        if author is not None:
            authorParam = '&author={}'.format(author)

        classifySearch = "{}{}{}".format(classifyRoot, titleParam, authorParam)

    return '{}&wskey={}&summary=false'.format(classifySearch, os.environ['OCLC_KEY'])
