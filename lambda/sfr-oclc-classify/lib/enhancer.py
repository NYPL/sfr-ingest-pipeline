import os

from helpers.errorHelpers import OCLCError, DataError
from helpers.logHelpers import createLog
from lib.dataModel import Identifier
from lib.readers.oclcClassify import classifyRecord
from lib.parsers.parseOCLC import readFromClassify, extractAndAppendEditions
from lib.outputManager import OutputManager

logger = createLog('enhancer')


def enhanceRecord(record):
    """Takes a single input record and retrieves data from the OCLC Classify
    service. Manages the overall workflow of the function."""

    try:
        workUUID = record['uuid']
        searchType = record['type']
        searchFields = record['fields']
        startPos = record.get('start', 0)
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
        classifyData = classifyRecord(
            searchType, searchFields, workUUID, start=startPos
        )

        # Step 2: Parse the data recieved from Classify into the SFR data model
        classifiedWork, instanceCount, oclcNo = readFromClassify(
            classifyData, workUUID
        )
        logger.debug('Instances found {}'.format(instanceCount))
        if instanceCount > 500:
            iterStop = startPos + instanceCount
            if instanceCount > 1500:
                iterStop = startPos + 1500
            for i in range(startPos + 500, iterStop, 500):
                classifyPage = classifyRecord(
                    searchType, searchFields, workUUID, start=i
                )
                extractAndAppendEditions(classifiedWork, classifyPage)

        if instanceCount > startPos + 1500:
            OutputManager.putQueue({
                'type': 'identifier',
                'uuid': workUUID,
                'fields': {
                    'idType': 'oclc',
                    'identifier': oclcNo,
                    'start': startPos + 1500
                }
            }, os.environ['CLASSIFY_QUEUE'])

        # This sets the primary identifier for processing by the db manager
        classifiedWork.primary_identifier = Identifier('uuid', workUUID, 1)

        # Step 3: Output this block to kinesis
        outputObject = {
            'status': 200,
            'type': 'work',
            'method': 'update',
            'data': classifiedWork
        }
        while len(classifiedWork.instances) > 100:
            instanceChunk = classifiedWork.instances[0:100]
            del classifiedWork.instances[0:100]
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
        OutputManager.putKinesis(
            outputObject, os.environ['OUTPUT_KINESIS'], workUUID
        )

    except OCLCError as err:
        logger.error('OCLC Query for work {} failed with message: {}'.format(
            workUUID, err.message
        ))
        raise err

    return True
