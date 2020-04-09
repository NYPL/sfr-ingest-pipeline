from datetime import datetime
from internetarchive import get_session
import os
import requests

from .abstractReader import AbsSourceReader
from helpers.configHelpers import decryptEnvVar
from helpers.logHelpers import createLog
from lib.models.iaRecord import IAItem

logger = createLog('iaReader')


class IAReader(AbsSourceReader):
    def __init__(self, updateSince):
        self.updateSince = updateSince
        self.source = 'Internet Archive'
        self.works = []
        self.itemIDs = []
        self.iaSession = self.createSession()
        self.importCollections = os.environ.get('IA_COLLECTIONS', '').split(', ')

    def createSession(self):
        iaKey = decryptEnvVar('IA_ACCESS_KEY')
        iaSecret = decryptEnvVar('IA_SECRET_KEY')
        print(iaKey)
        print(iaSecret)
        return get_session(config={'s3': {'access': iaKey, 'secret': iaSecret}})

    def collectResourceURLs(self):
        logger.info('Fetching records from Internet Archive')
        for collection in self.importCollections:
            logger.info('Fetching records for collection {}'.format(collection))
            self.itemIDs.extend([
                item['identifier'] for item in self.iaSession.search_items(
                    'collection:{}'.format(collection)
                )
            ])
    
    def scrapeResourcePages(self):
        i = 0
        for i, itemID in enumerate(self.itemIDs):
            logger.info('Fetching metadata for record {}'.format(itemID))
            item = self.iaSession.get_item(itemID)

            self.scrapeRecordMetadata(itemID, item)
            
            if i > 2:
                break

            i += 1

    def scrapeRecordMetadata(self, itemID, item):
        dateUpdated = datetime.strptime(
            item.metadata['updatedate'], '%Y-%m-%d %H:%M:%S'
        )
        if dateUpdated > self.updateSince:
            self.transformMetadata(itemID, item.metadata)

    def transformMetadata(self, itemID, itemData):
        logger.info('Transforming data into SFR transmission format')
        iaItem = IAItem(itemID, itemData)


        # Create Basic Work/Instance/Item structure
        iaItem.createStructure()

        # Parse identifiers an assign to proper records
        iaItem.parseIdentifiers()

        # Parse subjects, splitting and attaching to the work record
        iaItem.parseSubjects()

        # Parse agents, adding authors to work, publisher to instance, etc.
        iaItem.parseAgents()

        # Parse rights, assign to item and instance
        iaItem.parseRights()

        # Parse languages, generating ISO codes and attaching to work and instance
        iaItem.parseLanguages()

        # Parse publication date and add to instance
        iaItem.parseDates()
        
        # Parse read online and download links for item
        iaItem.parseLinks()

        # Parse list of summary fields into single joined string
        iaItem.parseSummary()

        # Fetch and add cover to instance
        iaItem.addCover()

        # Merge records into work and return
        iaItem.instance.formats.append(iaItem.item)
        iaItem.work.instances.append(iaItem.instance)

        logger.info('Saving work {} for ingest stream'.format(iaItem.work))
        self.works.append(iaItem.work)
