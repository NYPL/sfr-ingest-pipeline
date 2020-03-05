import re
import requests


class FrontierParser:
    REGEX = '(?:www|journal)\.frontiersin\.org\/research-topics\/([0-9]+)\/([a-zA-Z0-9\-]+)'
    LINK_STRINGS = {
        'https://www.frontiersin.org/research-topics/{}/epub': {
            'flags': {
                'local': False,
                'download': True,
                'ebook': True,
                'images': True
            },
            'media_type': 'application/epub+zip'
        },
        'https://www.frontiersin.org/research-topics/{}/pdf': {
            'flags': {
                'local': False,
                'download': True,
                'ebook': True,
                'images': True
            },
            'media_type': 'application/pdf'
        }
    }

    def __init__(self, uri, media_type):
        self.uri = uri
        self.media_type = media_type
    
    def validateURI(self):
        match = re.search(self.REGEX, self.uri)
        if match is not None:
            self.identifier = match.group(1)
            return True
        
        return False
    
    def createLinks(self):
        links = []
        for urlStr, attrs in self.LINK_STRINGS.items():
            outFile = None
            if 'epub' in urlStr:
                headReq = requests.head(urlStr.format(self.identifier))
                if headReq.status_code == 200:
                    try:
                        dispHeader = headReq.headers['content-disposition']
                        filename = re.search(r'filename=(.+)\.EPUB$', dispHeader).group(1)
                    except AttributeError:
                        print('Unable to load filename from {}'.format(dispHeader))
                        continue
                    outFile = '{}_{}.epub'.format(
                        self.identifier, filename.lower()
                    )
            links.append((
                urlStr.format(self.identifier),
                attrs['flags'],
                attrs['media_type'],
                outFile
            ))
        
        return links
