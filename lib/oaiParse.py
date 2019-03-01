from lxml import etree
import marcalyx

from helpers.errorHelpers import OAIFeedError, MARCXMLError
from helpers.logHelpers import createLog

logger = createLog('oai_parser')

# Standard namespaces used by the DOAB OAI-PMH feed
OAI_NS = '{http://www.openarchives.org/OAI/2.0/}'
MARC_NS = '{http://www.loc.gov/MARC21/slim}'


def parseOAI(oaiFeed):
    """Parse a supplied lxml object into a set of records, which are then read
    into a list of marcalyx records. 

    This also checks the provided feed for a resumption token, which if found,
    will be used to recursively retrieve the next page of DOAB records
    """
    try:
        logger.info('Parsing OAI-PMH feed of MARCXML records')
        res = etree.XML(oaiFeed)
    except etree.ParseError as err:
        logger.error('Unable to parse OAI-PMH Feed with lxml')
        logger.debug(err)
        raise OAIFeedError('Unable to parse XML from OAI-PMH feed')

    logger.info('Loading all retrieved MARCXML records')
    records = res.findall('.//{}record'.format(OAI_NS))
    marcRecords = list(filter(None, (readRecord(r) for r in records)))

    resToken = getResumptionToken(res)
    return resToken, marcRecords
        

def readRecord(record):
    """Accepts a single XML record and attempts to extract several header
    fields and then parse the main record using marcalyx. Returns
    recordID: The unique DOAB identifier for this record
    dateIssued: The datetime the record was last updated in DOAB
    marcRecord: A marxalyx object containing parsed MARC data
    """ 
    recordID = record.findtext('.//{}identifier'.format(OAI_NS))
    logger.info('Loading DOAB record {}'.format(recordID))
    
    recordHead = record.find('.//{}header'.format(OAI_NS))
    if recordHead.get('status') == 'deleted':
        logger.info('DOAB record flagged as deleted, skip.')
        return None
    
    dateIssued = recordHead.find('.//{}datestamp'.format(OAI_NS)).text
    
    logger.info('Parsing record with marcalyx')
    try:
        marcRecord = marcalyx.Record(record.find('.//{}record'.format(MARC_NS)))
    except TypeError as err:
        logger.error('Unable to parse MARCXML record {}'.format(recordID))
        logger.debug(err)
        return None
    
    logger.info('transforming {} into SFR data model'.format(marcRecord.titleStatement()))

    return (recordID, dateIssued, marcRecord)

def getResumptionToken(oaiFeed):
    """Attempt to load a resumptionToken from the current OAI-PMH feed. If 
    not found return None.
    """
    try:
        return oaiFeed.find('.//{}resumptionToken'.format(OAI_NS)).text
    except AttributeError:
        logger.warning('resumptionToken not found, will not load further pages')
        return None
