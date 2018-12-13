import json
from lxml import etree
from itertools import repeat

from helpers.errorHelpers import OCLCError
from helpers.logHelpers import createLog
from lib.dataModel import Agent
from lib.readers.oclcClassify import classifyRecord
from lib.parsers.parseOCLC import readFromClassify
from lib.kinesisWrite import KinesisOutput

logger = createLog('enhancer')

def enhanceRecord(record):
    try:
        source = record['source']
        recID = record['recordID']
        data = record['data']
    except KeyError as e:
        logger.error('Missing attribute in data block!')
        logger.debug(e)
        return False

    logger.info('Starting to enhance record {} from {}'.format(recID, source))
    try:

        # Step 1: Generate a set of XML records retrieved from Classify
        # This step also adds the oclc identifiers to the sourceData record
        classifyData, sourceData = classifyRecord(source, data, recID)

        # Step 2: Parse the data recieved from Classify into the SFR data model
        parsedData = readFromClassify(classifyData)

        # Step 3: Merge this data with the source data
        mergedData = mergeData(sourceData, parsedData)

        # Step 4: Output this block to kinesis
        KinesisOutput.putRecord(mergedData)

    except OCLCError as err:
        logger.error('OCLC Query failed with message: {}'.format(err.message))
        return False
    return True


def mergeData(data, oclcData):

    # Add official title and merge altTitle lists
    sourceTitle = data['title']
    data['title'] = oclcData['workTitle']
    altTitles = oclcData['altTitles']

    if sourceTitle not in altTitles:
        altTitles.append(sourceTitle)

    if data['altTitle'] not in altTitles:
        altTitles.append(data['altTitle'])

    data['altTitle'] = altTitles

    # Extend instances with OCLC editions
    # TODO Check to see if these can be merged, though this may be better
    # done in the next OCLC or even a normalization step
    data['instances'].extend(oclcData['editions'])

    # Merge agents with those found in OCLC, checking if their names pass a
    # certain threshhold
    mergedAgents = Agent.checkForMatches(oclcData['authors'], data['agents'])
    data['agents'] = list(mergedAgents)

    # Copy subjects from OCLC
    data['subjects'].extend(oclcData.subjects)

    # Copy measurements from OCLC
    data['measurements'].extend(oclcData.measurements)

    return data
