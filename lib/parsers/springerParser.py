import re
import requests


class SpringerParser:
    REGEX = 'link.springer.com\/book\/(10\.[0-9]+)\/([0-9\-]+)'
    REDIRECT_REGEX = '((?:https?:\/\/)?link\.springer\.com\/.+)$'
    LINK_STRINGS = {
        'https://link.springer.com/download/epub/{}/{}.epub': {
            'flags': {
                'local': False,
                'download': True,
                'ebook': True,
                'images': True
            },
            'media_type': 'application/epub+zip'
        },
        'https://link.springre.com/content/pdf/{}/{}.pdf': {
            'flags': {
                'local': False,
                'download': False,
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
        try:
            match = re.search(self.REGEX, self.uri)
            self.code = match.group(1)
            self.identifier = match.group(2)
            return True
        except (IndexError, AttributeError):
            redirectMatch = re.search(self.REDIRECT_REGEX, self.uri)
            if redirectMatch:
                self.uri = redirectMatch.group(1)
            else:
                return False
            
            if 'http' not in self.uri:
                self.uri = 'http://{}'.format(self.uri)
            
            redirectHeader = requests.head(self.uri)
            self.uri = redirectHeader.headers['Location']
            return self.validateURI()

    def createLinks(self):
        return [
            (
                urlStr.format(self.code, self.identifier),
                attrs['flags'],
                attrs['media_type'],
                None
            )
            for urlStr, attrs in self.LINK_STRINGS.items()
        ]
