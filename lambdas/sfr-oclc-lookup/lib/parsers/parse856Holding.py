import math
from multiprocessing import Process, Pipe
from multiprocessing.connection import wait
import re
import requests

from helpers.errorHelpers import HoldingError
from lib.dataModel import Link, Identifier


class HoldingParser:
    EBOOK_REGEX = {
        'gutenberg': r'gutenberg.org\/ebooks\/[0-9]+\.epub\.(?:no|)images$',
        'internetarchive': r'archive.org\/details\/[a-z0-9]+$',
        'hathitrust': r'catalog.hathitrust.org\/api\/volumes\/[a-z]{3,6}\/[a-zA-Z0-9]+\.html'  # noqa: E501
    }
    
    ID_REGEX = {
        'oclc': r'oclc\/([0-9]+)',
        'gutenberg': r'gutenberg.org\/ebooks\/([0-9]+)$'
    }

    URI_ID_REGEX = r'\/((?:(?!\/)[^.])+(?=$|\.[a-z]{3,4}$))'

    HATHI_OCLC_REGEX = r'([a-z]+\/[a-z0-9]+)\.html$'

    HATHI_ID_REGEX = r'id=([a-z\.\/\$0-9]+)'

    HATHI_DOWNLOAD_URL = 'babel.hathitrust.org/cgi/imgsrv/download/pdf?id={}'
    HATHI_METADATA_URL = 'http://catalog.hathitrust.org/api/volumes/full/{}.json' 
    def __init__(self, field, instance):
        self.field = field
        self.instance = instance
        self.source = 'unknown'
    
    def parseField(self):
        if self.field.ind1 != '4':
            raise HoldingError('856 does not contain an HTTP reference')

        try:
            self.uri = self.field.subfield('u')[0].value
        except IndexError:
            raise HoldingError('856 Field is missing u subfield for URI')
        
        self.identifier = self.loadURIid()
    
    def loadURIid(self):
        """Regex to extract identifier from an URI. \/((?:(?!\/)[^.])+ matches
        the path of the URI, excluding anything before the final slash (e.g.
        will match "1234" from http://test.com/1234) (?=$|\.[a-z]{3,4}$)) is a
        positive lookahead that excludes the file format from the identifier
        (so the above will still return "1234" if the URI ends in "1234.epub")
        """
        uriGroup = re.search(self.URI_ID_REGEX, self.uri)
        if uriGroup is not None:
            self.identifier = uriGroup.group(1)
        else:
            self.identifier = self.uri
    
    def extractBookLinks(self):
        if self.matchEbook() is True:
            return
        elif self.matchIdentifier() is True:
            return
        else:
            self.instance.links.append(
                HoldingParser.createLink(self.uri, 'text/html')
            )

    def matchEbook(self):
        for source, regex in self.EBOOK_REGEX.items():
            self.source = source
            if re.search(regex, self.uri):
                if source == 'internetarchive':
                    if self.checkIAStatus() is True:
                        return None
                elif source == 'hathitrust':
                    self.parseHathiLink()
                    return None

                self.instance.addFormat(**{
                    'source': source,
                    'content_type': 'ebook',
                    'links': [
                        self.createLink(
                            self.uri, 'text/html',
                            local=False, download=False, images=False, ebook=True
                        )
                    ],
                    'identifiers': [Identifier(identifier=self.identifier, source='hathi')]
                })
                return True
    
    def matchIdentifier(self):
        for idType, regex in self.ID_REGEX.items():
            idGroup = re.search(regex, self.uri)
            if idGroup is not None:
                self.instance.addIdentifier(**{
                    'type': idType,
                    'identifier': idGroup.group(1),
                    'weight': 0.8
                })
                return True

    def checkIAStatus(self):
        metadataURI = self.uri.replace('details', 'metadata')
        metadataResp = requests.get(metadataURI)
        if metadataResp.status_code == 200:
            iaData = metadataResp.json()
            iaMeta = iaData['metadata']
            if iaMeta.get('access-restricted-item', False) is False:
                return False
        
        return True
    
    def parseHathiLink(self):
        if 'catalog' not in self.uri:
            return None
        self.loadCatalogLinks()
    
    def loadCatalogLinks(self):
        hathiIDGroup = re.search(self.HATHI_OCLC_REGEX, self.uri)
        if hathiIDGroup:
            hathiID = hathiIDGroup.group(1)
            hathiItems = self.fetchHathiItems(hathiID)
            if hathiItems:
                self.startHathiMultiprocess(hathiItems)
    
    def startHathiMultiprocess(self, hathiItems):
        processes = []
        outPipes = []
        cores = 4

        chunkSize = math.ceil(len(hathiItems) / cores)

        for i in range(cores):
            start = i * chunkSize
            end = start + chunkSize

            pConn, cConn = Pipe(duplex=False)
            proc = Process(
                target=self.processHathiChunk,
                args=(hathiItems[start:end], cConn)
            )
            processes.append(proc)
            outPipes.append(pConn)
            proc.start()
            cConn.close()

        while outPipes:
            for p in wait(outPipes):
                try:
                    newItem = p.recv()
                    if newItem == 'DONE':
                        outPipes.remove(p)
                    else:
                        self.instance.addFormat(**newItem) 
                except EOFError:
                    outPipes.remove(p)

        for proc in processes:
            proc.join()

    def fetchHathiItems(self, hathiID):
        apiURL = self.HATHI_METADATA_URL.format(
            hathiID
        )
        apiResp = requests.get(apiURL)
        if apiResp.status_code == 200:
            catalogData = apiResp.json()
            return catalogData.get('items', [])
    
    def processHathiChunk(self, hathiItems, cConn):
        for recItem in hathiItems:
            newItem = self.getNewItemLinks(recItem)
            if newItem is not None:
                cConn.send(newItem)
        
        cConn.send('DONE')
        cConn.close()

    def getNewItemLinks(self, recItem):
        if recItem.get('rightsCode', 'ic') in ['ic', 'icus', 'ic-world', 'und']:
            return
        redirectURL = requests.head(recItem['itemURL'])
        realURL = redirectURL.headers['Location'].replace('https://', '')

        hathiID = re.search(self.HATHI_ID_REGEX, realURL).group(1)
        downloadURL = self.HATHI_DOWNLOAD_URL.format(hathiID)

        return {
            'source': self.source,
            'content_type': 'ebook',
            'links': [
                HoldingParser.createLink(
                    realURL, 'text/html',
                    local=False, download=False, images=True, ebook=False
                ),
                HoldingParser.createLink(
                    downloadURL, 'application/pdf',
                    local=False, download=True, images=True, ebook=False
                )
            ],
            'identifiers': [Identifier(identifier=hathiID, source='hathi')]
        }

    @staticmethod
    def createLink(uri, mediaType, local=False, download=False, images=False, ebook=False):
        return Link(
            url=uri,
            mediaType=mediaType,
            flags={'local': local, 'download': download, 'images': images, 'ebook': ebook}
        )
