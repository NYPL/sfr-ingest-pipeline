import os
import requests

from .abstractReader import AbsSourceReader
from lib.models.metRecord import MetItem
from helpers.logHelpers import createLog

logger = createLog('metReader')


class MetReader(AbsSourceReader):
    INDEX_URL = 'https://libmma.contentdm.oclc.org/digital/api/search/collection/p15324coll10/order/title/ad/asc/page/{}/maxRecords/50'
    ITEM_API = 'https://libmma.contentdm.oclc.org/digital/api/collections/p15324coll10/items/{}/false'
    def __init__(self, updateSince):
        self.updateSince = updateSince
        self.startPage = 1
        self.stopPage = 48
        self.source = 'Metropolitan Museum of Art'
        self.works = []
        self.itemIDs = []
    
    def collectResourceURLs(self):
        logger.info('Fetching records from MET Digital Collections')
        for page in range(self.startPage, self.stopPage):
            logger.debug('Fetching page {}'.format(page))
            indexResp = requests.get(self.INDEX_URL.format(page))
            indexData = indexResp.json()
            for item in indexData['items']:
                itemID = item['itemId']
                logger.debug('Found record with ID {}'.format(itemID))
                self.itemIDs.append(itemID)
    
    def scrapeResourcePages(self):
        for itemID in self.itemIDs:
            logger.info('Fetching metadata for record {}'.format(itemID))
            pageResp = requests.get(self.ITEM_API.format(itemID))
            pageData = pageResp.json()

            self.works.append(self.scrapeRecordMetadata(itemID, pageData))

    def scrapeRecordMetadata(self, itemID, pageData):
        logger.debug('Extracting data from record {}'.format(itemID))

        # Create local MET record to hold intermediate data
        parentID = pageData['parentId']
        if parentID != -1:
            itemID = parentID
        newItem = MetItem(itemID, pageData)

        # Extract data from MET API format
        newItem.extractRelevantData()

        # Transform extracted data into SFR model
        return self.transformMetadata(newItem)
    
    def transformMetadata(self, metItem):
        logger.info('Transforming data into SFR transmission format')

        # Create Basic Work/Instance/Item structure
        metItem.createStructure()

        # Parse identifiers an assign to proper records
        metItem.parseIdentifiers()

        # Parse subjects, splitting and attaching to the work record
        metItem.parseSubjects()

        # Parse agents, adding authors to work, publisher to instance, etc.
        metItem.parseAgents()

        # Parse rights, assign to item and instance
        metItem.parseRights()

        # Parse languages, generating ISO codes and attaching to work and instance
        metItem.parseLanguages()

        # Parse publication date and add to instance
        metItem.parseDates()
        
        # Parse read online and download links for item
        metItem.parseLinks()

        # Fetch and add cover to instance
        metItem.addCover()

        # Merge records into work and return
        metItem.instance.formats.append(metItem.item)
        metItem.work.instances.append(metItem.instance)

        logger.info('Returning work {} to be sent to ingest stream'.format(metItem.work))
        return metItem.work
