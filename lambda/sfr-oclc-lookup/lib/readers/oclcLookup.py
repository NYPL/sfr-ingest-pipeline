import requests
from requests.exceptions import Timeout, ConnectionError
import os
from lxml import etree
import marcalyx

from helpers.errorHelpers import OCLCError
from helpers.logHelpers import createLog

logger = createLog('oclc_lookup')

NAMESPACE = {
    None: 'http://classify.oclc.org'
}


def lookupRecord(identifier):
    """Looks up an OCLC# in the OCLC Catalog API.
    Returns a MARCXML record."""

    # TODO Cache this somewhere?
    queryURL = createURL(identifier)
    logger.info('Fetching data for url: {}'.format(queryURL))

    # Load Query Response from OCLC Classify
    logger.debug('Making OCLC Catalog request for {}'.format(identifier))
    marcData = catalogLookup(queryURL)

    # Parse response, and if it is a Multi-Work response, parse further
    logger.debug('Parsing Classify Response')
    return parseMARC(marcData)


def parseMARC(marcData):
    """Parses raw MARCXML data into a marcalyx record that can be used
    to extract all metadata from record"""
    try:
        parseMARC = etree.fromstring(marcData.encode('utf-8'))
    except etree.XMLSyntaxError as err:
        logger.error('OCLC Catalog returned invalid XML')
        logger.debug(err)
        raise OCLCError('Received invalid XML from OCLC service')

    try:
        record = marcalyx.Record(parseMARC)
    except IndexError as err:
        logger.error('marcalyx failed to parse entry for catalog entry')
        logger.debug(err)
        raise OCLCError('MARCXML could not be parsed by marcalyx')

    return record


def catalogLookup(queryURL):
    """Execute a request against the OCLC Catalog service"""
    try:
        classifyResp = requests.get(queryURL, timeout=2)
    except (Timeout, ConnectionError):
        logger.warning('Failed to query URL {}'.format(queryURL))
        classifyResp = requests.get(queryURL, timeout=5)

    if classifyResp.status_code != 200:
        logger.error('OCLC Catalog Request failed with status {}'.format(
            classifyResp.status_code
        ))
        logger.debug(classifyResp.text)
        raise OCLCError('Failed to reach OCLC Catalog Service')

    classifyBody = classifyResp.text
    return classifyBody


def createURL(identifier):
    """Create a URL query OCLC Catalog Lookup service"""
    catalogRoot = 'http://www.worldcat.org/webservices/catalog/content'
    catalogQuery = '{}/{}?wskey={}'.format(
        catalogRoot,
        identifier,
        os.environ['OCLC_KEY']
    )
    return catalogQuery
