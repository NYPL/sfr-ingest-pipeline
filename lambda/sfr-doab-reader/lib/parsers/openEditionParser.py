import re
import requests

from bs4 import BeautifulSoup


class OpenEditionParser:
    ORDER = 2
    OE_URL_ROOT = 'books.openedition.org'
    REGEX = r'books.openedition.org/([a-z0-9]+)/([0-9]+)$'
    OPTION_REGEXES = [
        r'\/(epub\/[0-9]+)', r'\/(pdf\/[0-9]+)', r'([0-9]+\?format=reader)$', r'^([0-9]+)$'
    ]
    FORMAT_ATTRS = [
        {
            'media_type': 'application/epub+zip',
            'flags': {'local': False, 'download': True, 'images': True, 'ebook': True}
        },
        {
            'media_type': 'application/pdf',
            'flags': {'local': False, 'download': True, 'images': True, 'ebook': True}
        },
        {
            'media_type': 'text/html',
            'flags': {'local': False, 'download': False, 'images': True, 'ebook': True}
        },
        {
            'media_type': 'text/html',
            'flags': {'local': False, 'download': False, 'images': True, 'ebook': True}
        }
    ]

    def __init__(self, uri, media_type):
        self.uri = uri
        self.media_type = media_type
    
    @property
    def uri(self):
        return self._uri
    
    @uri.setter
    def uri(self, value):
        if value[:4] == 'http':
            self._uri = value
        else:
            self._uri = 'http://{}'.format(value)
    
    def validateURI(self):
        match = re.search(self.REGEX, self.uri)
        if match is not None:
            if match.start() > 8:
                self.uri = self.uri[match.start():]
            self.publisher = match.group(1)
            self.identifier = match.group(2)
            return True
        
        return False
    
    def createLinks(self):
        options = []
        oePage = requests.get(self.uri)
        if oePage.status_code == 200:
            for link in self.loadEbookLinks(oePage.text):
                self.parseBookLink(options, link)

        return self.getBestLink(options)
            

    def loadEbookLinks(self, oeHTML):
        oeSoup = BeautifulSoup(oeHTML, 'html.parser')
        accessEl = oeSoup.find(id='book-access')
        return accessEl.find_all('a')
    
    def parseBookLink(self, options, link):
        relLink = link.get('href')
        for i, regex in enumerate(self.OPTION_REGEXES):
            typeMatch = re.search(regex, relLink)
            if typeMatch:
                formatAttrs = self.FORMAT_ATTRS[i]
                options.append((
                    i,
                    '{}/{}/{}'.format(self.OE_URL_ROOT, self.publisher, typeMatch.group(1)),
                    formatAttrs['flags'],
                    formatAttrs['media_type'],
                    '{}_{}.epub'.format(self.publisher, self.identifier)
                ))
    
    def getBestLink(self, options):
        options.sort(key=lambda x: x[0])
        try:
            topOption = options[0]
            return topOption[1:]
        except IndexError:
            return []
