import json
import os
import re
import requests
import time

from lxml import etree

from helpers.logHelpers import createLog
from helpers.errorHelpers import UnglueError


class Unglueit():
    def __init__(self, isbn):
        self.isbn = isbn
        self.logger = createLog('unglueit')
        self.unglueitSearch = os.environ['ISBN_LOOKUP']
        self.unglueitFetch = os.environ['OPDS_LOOKUP']
        self.unglueitUser = os.environ['USERNAME']
        self.unglueitApiKey = os.environ['API_KEY']

        self.logger.info('Fetching summary for {}'.format(self.isbn))

    def validate(self):
        checkISBN = str(self.isbn.replace('-', '').strip())
        if not re.match(r'^[0-9X]+$', checkISBN):
            raise UnglueError(500, 'Supplied ISBN contains invalid characters')

        if len(checkISBN) == 10:
            Unglueit.validateISBN10(checkISBN)
        elif len(checkISBN) == 13:
            Unglueit.validateISBN13(checkISBN)
        else:
            raise UnglueError(
                500,
                'ISBNs must be either 10 or 13 characters long'
            )

    @staticmethod
    def validateISBN10(isbn):
        checkDig = isbn[-1:]
        checkDig = 10 if checkDig == 'X' else int(checkDig)
        isbn = isbn[:-1]
        calcTotal = sum([int(isbn[i]) * (10 - i) for i in range(len(isbn))])
        if (11 - (calcTotal % 11)) != checkDig:
            raise UnglueError(500, 'ISBN fails validation ISBN-10 algorithm')

    @staticmethod
    def validateISBN13(isbn):
        try:
            checkDig = int(isbn[-1:])
            if checkDig == 0:
                checkDig = 10
        except ValueError:
            raise UnglueError(500, 'ISBN-13 check digit must be an integer')
        isbn = isbn[:-1]
        calcTotal = sum([
            int(isbn[i]) if i % 2 == 0 else int(isbn[i]) * 3
            for i in range(len(isbn))
        ])
        if (10 - (calcTotal % 10)) != checkDig:
            raise UnglueError(500, 'ISBN fails ISBN-13 algorithm')

    def fetchSummary(self):
        workID = self.getWork()
        summary = self.getSummary(workID)
        return Unglueit.formatResponse(200, {
            'match': True,
            'isbn': self.isbn,
            'summary': summary
        })

    def getWork(self):
        self.logger.info('Querying unglue.it for work record related to ISBN')
        req = requests.get('{}&username={}&api_key={}&value={}'.format(
            self.unglueitSearch,
            self.unglueitUser,
            self.unglueitApiKey,
            self.isbn
        ))

        if req.status_code != 200:
            self.logger.warning('Received non-200 error from unglue.it search')
            self.logger.debug(req.body)
            raise UnglueError(500, 'Error in unglue.it Search API')

        response = req.json()
        try:
            print(response)
            work = response['objects'][0]
            return re.search(r'\/([0-9]+)\/', work['work']).group(1)
        except (AttributeError, IndexError):
            raise UnglueError(404, {
                'match': False,
                'message': 'No record found in unglue.it for {}'.format(
                    self.isbn
                )
            })

    def getSummary(self, workID):
        self.logger.info('Fetching OPDS record for unglue.it work {}'.format(
            workID
        ))
        req = requests.get('{}{}'.format(self.unglueitFetch, workID))

        if req.status_code != 200:
            self.logger.warning('Received non-200 error from unglue.it OPDS')
            self.logger.debug(req.body)
            raise UnglueError(500, 'Error in unglue.it OPDS API')

        return self.parseOPDS(req.text)

    def parseOPDS(self, opds):
        marcRoot = etree.fromstring(opds)
        nsmap = marcRoot.nsmap
        opdsEntry = marcRoot.find('{' + nsmap[None] + '}entry')
        opdsContent = opdsEntry.find('{' + nsmap[None] + '}content')
        return opdsContent.text

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
