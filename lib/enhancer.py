import os

from helpers.errorHelpers import OCLCError, DataError
from helpers.logHelpers import createLog
from lib.dataModel import Agent, Identifier
from lib.readers.oclcClassify import classifyRecord
from lib.parsers.parseOCLC import readFromClassify
from lib.outputManager import OutputManager

logger = createLog('enhancer')

def enhanceRecord(record):
    """Takes a single input record and retrieves data from the OCLC Classify
    service. Manages the overall workflow of the function."""

    try:
        workUUID = record['uuid']
        searchType = record['type']
        searchFields = record['fields']
    except KeyError as e:
        logger.error('Missing attribute in data block!')
        logger.debug(e)
        raise DataError('Required attribute missing from data block')
    except TypeError as e:
        logger.error('Could not read data from source')
        logger.debug(e)
        raise DataError('Kinesis data contains non-dictionary value')

    logger.info('Starting to enhance work record {}'.format(workUUID))

    try:
        # Step 1: Generate a set of XML records retrieved from Classify
        # This step also adds the oclc identifiers to the sourceData record
        classifyData = classifyRecord(searchType, searchFields, workUUID)

        # Step 2: Parse the data recieved from Classify into the SFR data model
        parsedData = readFromClassify(classifyData, workUUID)

        # This sets the primary identifier for processing by the db manager
        parsedData.primary_identifier = Identifier('uuid', workUUID, 1)

        # Step 3: Output this block to kinesis
        outputObject = {
            'status': 200,
            'type': 'work',
            'method': 'update',
            'data': parsedData
        }
        while len(parsedData.instances) > 100:
            instanceChunk = parsedData.instances[0:100]
            del parsedData.instances[0:100]
            OutputManager.putKinesis(
                {
                    'status': 200,
                    'type': 'work',
                    'method': 'update',
                    'data': {
                        'instances': instanceChunk,
                        'primary_identifier': Identifier('uuid', workUUID, 1)
                    }
                },
                os.environ['OUTPUT_KINESIS'],
                workUUID
            )

        OutputManager.putKinesis(outputObject, os.environ['OUTPUT_KINESIS'], workUUID)

    except OCLCError as err:
        logger.error('OCLC Query for work {} failed with message: {}'.format(workUUID, err.message))
        raise err

    return True
