import os

from helpers.errorHelpers import OCLCError
from helpers.logHelpers import createLog
from lib.dataModel import Agent, Identifier
from lib.readers.oclcClassify import classifyRecord
from lib.parsers.parseOCLC import readFromClassify
from lib.kinesisWrite import KinesisOutput

logger = createLog('enhancer')

def enhanceRecord(record):
    try:
        sourceData = record['data']
    except KeyError:
        logger.error('Missing data from input event')
        return False

    try:
        workUUID = sourceData['uuid']
        searchType = sourceData['type']
        searchFields = sourceData['fields']
    except KeyError as e:
        logger.error('Missing attribute in data block!')
        logger.debug(e)
        return False
    except TypeError as e:
        logger.error('Could not read data from source')
        logger.debug(e)
        return False

    logger.info('Starting to enhance work record {}'.format(workUUID))
    try:

        # Step 1: Generate a set of XML records retrieved from Classify
        # This step also adds the oclc identifiers to the sourceData record
        classifyData = classifyRecord(searchType, searchFields, workUUID)

        if classifyData is None:
            # If we got no data back, then either we got no data, or this was
            # a multi-work response and the records have been put back into the
            # queue
            logger.info('No data for parsing related to {}, exit'.format(workUUID))
            return False

        # Step 2: Parse the data recieved from Classify into the SFR data model
        parsedData = readFromClassify(classifyData)

        parsedData.primary_identifier = Identifier('uuid', workUUID, 1)

        # Step 3: Output this block to kinesis
        KinesisOutput.putRecord(parsedData, os.environ['OUTPUT_KINESIS'])

    except OCLCError as err:
        logger.error('OCLC Query failed with message: {}'.format(err.message))
        return False
    return True
