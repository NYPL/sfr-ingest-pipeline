from helpers.errorHelpers import OCLCError
from helpers.logHelpers import createLog
from lib.readers.oclcLookup import lookupRecord
from lib.parsers.parseOCLC import readFromMARC

logger = createLog('enhancer')


def fetchData(identifier, idenType):
    """Takes a single input identifier and queries the OCLC Lookup API for
    the corresponding record."""
    if idenType != 'oclc':
        logger.error('Catalog lookup requires an OCLC identifier')
        raise OCLCError('OCLC Catalog lookup requires an OCLC Number')

    logger.info('Loading MARC for record {}'.format(identifier))

    try:
        marcData = lookupRecord(identifier)
        parsedData = readFromMARC(marcData)
    except OCLCError as err:
        logger.error('OCLC Query failed with message: {}'.format(err.message))
        raise err

    return parsedData
