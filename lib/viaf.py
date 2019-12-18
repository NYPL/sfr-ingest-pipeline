import os
import time
import json
import requests
import redis
from urllib.parse import quote_plus

from helpers.logHelpers import createLog
from helpers.errorHelpers import VIAFError


class VIAFSearch():
    """Central class for the function that manages VIAF lookup queries,
    returning results either from the OCLC VIAF lookup API, the internal Redis
    cache that stores values which have been previously retrieved, or a non-200
    status code if no VIAF information can be found.
    """
    QUERY_TYPES = ['personal', 'corporate']

    def __init__(self, queryName, queryType):
        self.queryName = queryName
        self.queryType = queryType.lower() if queryType else 'personal'
        self.validateType()

        self.logger = createLog('viafSearch')
        self.viaf_endpoint = os.environ['VIAF_API']
        self.redis = redis.Redis(
            host=os.environ['REDIS_ARN'],
            port=6379,
            socket_timeout=5
        )

    def query(self):
        """Executes a VIAF query against OCLC/local cache and returns the
        result using the supplied name (personal/corporate).

        Returns:
            [dict] -- A response object containing a status and data to be
            returned.
        """

        self.logger.info('Querying OCLC/Redis for {}'.format(self.queryName))
        # Check to see if we've queried this name and found a VIAF ID
        cachedName = self.checkCache()
        if cachedName is not None:
            return VIAFSearch.formatResponse(
                200,
                {
                    key.decode('utf-8'): item.decode('utf=8')
                    for key, item in cachedName.items()
                }
            )

        # If not found in the cache, search the OCLC VIAF service for the name
        viafRecords = self.searchVIAF()
        return self.parseVIAF(viafRecords)

    def searchVIAF(self):
        """Searches the OCLC VIAF AutoSuggest endpoint for matching VIAF
        records. If found returns the top match, including the controlled name
        value, VIAF ID, and LCNAF ID.

        Raises:
            VIAFError: If the request to the OCLC API fails, raise error.

        Returns:
            [dict] -- Returns list of dicts, each containing a match from the
            OCLC VIAF lookup API.
        """
        self.logger.info('Searching OCLC API for {}'.format(self.queryName))
        req = requests.get('{}{}'.format(
            self.viaf_endpoint,
            quote_plus(self.queryName)
        ))
        if req.status_code != 200:
            self.logger.warning('Received non-200 error from OCLC')
            self.logger.debug(req.body)
            raise VIAFError('Error in OCLC VIAF API')

        return req.json().get('result', None)

    def parseVIAF(self, viafJSON):
        """Parses list of VIAF records received from OCLC and returns the first
        match, parsed to retrieve the relevant fields.

        Arguments:
            viafJSON {list} -- List of VIAF records returned for search term.

        Returns:
            [dict] -- A formatted response object containing a status and the
            relevant data for the SFR service.
        """
        self.logger.info('Parsing VIAF results for {}'.format(self.queryName))
        if viafJSON is None:
            self.logger.info('No matches found, return 404')
            return VIAFSearch.formatResponse(
                404,
                {'message': 'Could not find matching VIAF record'}
            )

        while True:

            try:
                match = viafJSON.pop(0)
            except IndexError:
                return VIAFSearch.formatResponse(
                    404,
                    {'message': 'Could not find record of matching type {}'.format(self.queryType)}
                )
            if match['nametype'] != self.queryType:
                continue

            self.logger.debug('Found matching record {}'.format(str(match)))
            viafData = {
                'name': match['displayForm'],
                'viaf': match.get('viafid', None),
                'lcnaf': match.get('lc', None)
            }
            break

        # Set this object in the cache
        self.setCache(viafData)

        self.logger.info('Returning top match to SFR pipeline')
        return VIAFSearch.formatResponse(200, viafData)

    def checkCache(self):
        """Queries the Redis cache for an existing VIAF object that corresponds
        to this agent string.

        Returns:
            [dict] -- Dictionary containing VIAF ID, LCANF ID and controlled
            name string from the VIAF service.
        """
        self.logger.debug('Checking for known VIAF # of {}'.format(
            self.queryName
        ))
        nameNumbers = self.redis.hgetall('{}/{}'.format(
            self.queryType, self.queryName
        ))

        if not len(nameNumbers.keys()):
            self.logger.debug('Did not find matching cache key')
            return None

        self.logger.debug('Found match in cache')
        return nameNumbers

    def setCache(self, viafObj):
        """Inserts a VIAF object for the current name string into the cache,
        allowing for faster lookups of this name in the future.

        Arguments:
            viafObj {dist} -- A dict containing the controlled form of the
            current name and the VIAF and LCNAF IDs.
        """
        cacheKey = '{}/{}'.format(self.queryType, self.queryName)
        self.logger.debug('Setting cache hash for {}'.format(cacheKey))
        viafObj = {
            key: item for key, item in viafObj.items() if item is not None
        }
        self.redis.hmset(cacheKey, viafObj)

    @staticmethod
    def formatResponse(status, data):
        """Creates a response block to be returned to the API client.

        Arguments:
            status {integer} -- A standard HTTP status code.
            data {dict} -- A dictionary containing either an error message or a
            set of metadata describing the agent being queried.

        Returns:
            [dict] -- A complete response object containing a status and
            relevant data.
        """
        return {
            'statusCode': status,
            'headers': {
                'req-time': time.time()
            },
            'isBase64Encoded': False,
            'body': json.dumps(data)
        }

    def validateType(self):
        if self.queryType not in self.QUERY_TYPES:
            raise VIAFError('queryType must be either personal or corporate')
