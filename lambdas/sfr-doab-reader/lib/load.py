import os
import json
import requests
from datetime import datetime, timedelta

from helpers.errorHelpers import OAIFeedError, DataError
from helpers.logHelpers import createLog

logger = createLog('oai_load')


class Loaders():

    def __init__(self):
        # Root of the DOAB OAI-PMH feed
        self.doab_root = os.environ['DOAB_OAI_ROOT']

        # Period over which to retrieve updated records from DOAB, in days
        tdSince = timedelta(days=int(os.environ['LOAD_DAYS_AGO']))
        self.load_since = datetime.now() - tdSince

        # Locally stored XML file containing MARC Relator codes
        self.relators_file = os.environ['MARC_RELATORS']

    def loadOAIFeed(self, resumptionToken=None):
        """Query OAI-PMH feed for updated records and return the text content
        if they are retrieved.

        If resumptionToken is provided, this is to load the next page of
        records for an already executed query. The root is the same, this
        merely applies different parameters to the url.
        """
        if resumptionToken is None:
            logger.debug('Loading initial batch of DOAB records')
            sinceStr = 'from={}'.format(self.load_since.strftime('%Y-%m-%d'))
            reqStr = '{}&metadataPrefix=marcxml'.format(sinceStr)
        else:
            logger.debug('Loading batch {} of DOAB records'.format(
                resumptionToken
            ))
            reqStr = 'resumptionToken={}'.format(resumptionToken)
        doabRes = requests.get('{}&{}'.format(
            self.doab_root,
            reqStr
        ))
        if doabRes.status_code != 200:
            logger.error('Failed to load OAI-PMH Feed')
            logger.debug(doabRes.text)
            raise OAIFeedError('OAI-PMH Load Error')
        
        return doabRes.content

    def loadOAIRecord(self, singleURL):
        """If the function has been invoked locally, use the supplied URL to 
        retrieve a single OAI-PMH record
        """
        doabRec = requests.get(singleURL)
        if doabRec.status_code != 200:
            raise OAIFeedError('Failed to Load Single OAI Record')

        return doabRec.content 

    def loadMARCRelators(self):
        """DOAB identifies contributors to its records using the MARC Relator
        codes. These are not available in a library anywhere and as a result
        these must be translated to human-readable formats. This parses the
        LoC's provided XML file into a dictionary of translated codes.
        """
        relRes = requests.get(self.relators_file)
        if relRes.status_code != 200:
            logger.error('Failed to load MARC21 Relator Authority')
            logger.debug(relRes.text)
            raise DataError('Unable to load necessary MARC21 Authority')
        
        relJSON = json.loads(relRes.content)

        terms = {}
        rdfLabel = 'http://www.loc.gov/mads/rdf/v1#authoritativeLabel'
        for rel in relJSON:
            try:
                code = rel['@id'].split('/')[-1]
                terms[code] = rel[rdfLabel][0]['@value']
            except KeyError:
                continue
        
        return terms