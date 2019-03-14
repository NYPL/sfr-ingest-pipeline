import csv
import gzip
import os
import requests
from datetime import datetime

from helpers.errorHelpers import ProcessingError, DataError, KinesisError
from helpers.logHelpers import createLog

from lib.hathiRecord import HathiRecord
from lib.countryParser import loadCountryCodes
from lib.kinesisWrite import KinesisOutput

# Logger can be passed name of current module
# Can also be instantiated on a class/method basis using dot notation
logger = createLog('handler')


def handler(event, context):
    """This method is invoked by the lambda trigger and governs overall
    execution of the function. The event and context variables are ignored in
    general invocations as they serve only to trigger the general execution
    of the function.

    In local/non-scheduled invocations, the event JSON block will contain the
    specific CSV file to load records from. These are special cases however.

    Beyond these invocation differences the function will parse the source
    records in the same manner
    """

    logger.info('Starting Lambda Execution')
    logger.info('Checking type of invocation {}'.format(
        event.get('source', 'scheduled'))
    )

    # Check if the event is set to have certain local-only characteristics
    # if it does, this is being run in a non-scheduled way on a local file.
    # Load the local file defined in the event, otherwise fetch file from Hathi

    columns = [
            'htid',
            'access',
            'rights',
            'bib_key',
            'description',
            'source',
            'source_id',
            'oclcs',
            'isbns',
            'issns',
            'lccns',
            'title',
            'publisher_pub_date',
            'rights_statement',
            'rights_determination_date',
            'gov_doc',
            'copyright_date',
            'pub_place',
            'language',
            'format',
            'collection_code',
            'provider_entity',
            'responsible_entity',
            'digitization_entity',
            'access_profile',
            'author'
        ]
    if event['source'] == 'local.file':
        logger.info('Loading records from local file')
        csvFile = loadLocalCSV(event['localFile'])
    else:
        logger.info('Checking for updates from HathiTrust TSV files')
        
        csvFile = fetchHathiCSV()
        logger.info('Returning {} records fetched from HathiTrust'.format(
            str(len(csvFile))
        ))
        if csvFile is None:
            logger.info('No daily update from HathiTrust. No actions to take')
            return [('empty', 'no updated records in retrieval period')]

    # This return will be reflected in the CloudWatch logs
    # but doesn't actually do anything

    logger.info('Parsing records from CSV/TSV file')

    output = fileParser(csvFile, columns)

    logger.info('Successfully invoked lambda')

    return output


def loadLocalCSV(localFile):
    """Load HathiTrust records from supplied local CSV file. This checks for
    the existence of a header row and skips if present

    Arguments:
    localFile -- path to a local CSV

    Output:
    rows -- list of parsed CSV rows
    """
    rows = []
    logger.debug('Opening {} containing hathiTrust records'.format(localFile))

    try:
        hathiFile = open(localFile, newline='')
    except FileNotFoundError:
        logger.error('Could find file at path {}'.format(localFile))
        raise ProcessingError('loadLocalCSV', 'Could not open local CSV file')

    with hathiFile:
        hathiReader = csv.reader(hathiFile)
        for row in hathiReader:
            if row[0] == 'htid':
                continue
            rows.append(row)
    logger.debug('Loaded {} rows from {}'.format(str(len(rows)), localFile))
    return rows


def fetchHathiCSV():
    logger.info('Fetching most recent update file from HathiTrust')
    fileList = requests.get(os.environ['HATHI_DATAFILES'])
    if fileList.status_code != 200:
        raise ProcessingError('Unable to load data files')
    
    logger.debug('Loaded JSON list of HathiFiles')
    fileJSON = fileList.json()

    logger.debug('Sorting JSON list of files by created date')
    fileJSON.sort(key=lambda x: datetime.strptime(x['created'], '%Y-%m-%dT%H:%M:%S-%f').timestamp(), reverse=True)
    for hathiFile in fileJSON:
        if hathiFile['full'] is False:
            logger.info('Found most recent file {} updated on {}'.format(
                hathiFile['url'],
                hathiFile['created']
            ))
            with open('tmp_hathi.txt.gz', 'wb') as hathiTSV:
                logger.debug('Storing Downloaded HathiFile in tmp_hathi.txt.gz')
                hathiReq = requests.get(hathiFile['url'])
                hathiTSV.write(hathiReq.content)
            break
    
    # At present we aren't downloading in-copyright works, so skip anything
    # that has these rights codes
    rightsSkips = ['ic', 'icus', 'ic-world', 'und']

    with gzip.open('tmp_hathi.txt.gz', 'rt') as unzipTSV:
        logger.debug('Parsing txt.gz file downloaded into TSV file')
        hathiTSV = csv.reader(unzipTSV, delimiter='\t')
        
        logger.debug('Parse for all rows to return')
        return [ r for r in hathiTSV if r[2] not in rightsSkips ]


def fileParser(fileRows, columns):
    """Iterates through parsed CSV rows to return a list of records formatted
    to comply with the SFR data format. As a requirement of this a dict of
    country codes/country names is generated here for use as a lookup table.

    Arguments:
    fileRows -- list of parsed CSV rows
    columns -- list of column names that correspond to the CSV file

    Output:
    outcomes -- list of processing result tuples from the rowParser() function.
    These are either 'success' or 'failure' and provide resiliency in logging
    errors while allowing this method to continue iteration over rows
    containing errors
    """

    logger.info('Parsing rows retrieved from source file')

    logger.debug('Loading country codes from XML file')
    countryCodes = loadCountryCodes()

    outcomes = []
    for row in fileRows:
        try:
            outcomes.append(rowParser(row, columns, countryCodes))
        except ProcessingError as err:
            outcomes.append(('failure', err.source, err.message))

    return outcomes


def rowParser(row, columns, countryCodes):
    """Parse single HathiTrust item entry (corresponding to an item-level
    record in the SFR model) into the SFR data model and pass the resulting
    object to Kinesis for introduction into the SFR data pipeline.

    This method is a manager that handles methods around a HathiRecord object.
    Each method creates/enhances a part of the SFR metadata object, allowing
    for the object to both be built up and its components easily treated
    as seperate components if necessary

    Arguments:
    row -- list of fields from the HathiTrust source CSV file
    columns -- list of columns that corresponds to the source row
    countryCodes -- dict of country code and name translations

    Output: None, writes resulting work record to a Kinesis stream
    """

    logger.info('Reading entry for HathiTrust item {}'.format(row[0]))

    logger.debug('Generating source dict from row and column names')
    # This quickly builds a dictionary with column names that can be used to
    # retrieve specific values
    hathiDict = dict(zip(columns, row))
    # Generate a hathi record object with the source dict
    hathiRec = HathiRecord(hathiDict)

    try:
        # Generate an SFR-compliant object
        hathiRec.buildDataModel(countryCodes)
    except DataError as err:
        logger.error('Unable to process record {}'.format(
            hathiRec.ingest['htid']
        ))
        logger.debug(err.message)
        raise ProcessingError('DataError', err.message)

    try:
        logger.debug('Writing hathi record {} to kinesis for ingest'.format(
            hathiRec.work.primary_identifier.identifier
        ))
        KinesisOutput.putRecord({
            'status': 200,
            'type': 'work',
            'method': 'insert',
            'data': hathiRec.work
        }, os.environ['OUTPUT_STREAM'])
    except KinesisError as err:
        logger.error('Unable to output record {} to Kinesis'.format(
            hathiRec.ingest['htid']
        ))
        logger.debug(err.message)
        raise ProcessingError('KinesisError', err.message)

    # On success, return tuple containg status and identifier, verifies record
    # was passed to next step in the data pipeline
    return ('success', 'HathiTrust Item {}'.format(hathiRec.ingest['htid']))
