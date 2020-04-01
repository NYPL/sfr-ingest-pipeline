import re
import requests


class DeGruyterParser:
    ORDER = 5
    REGEX = 'www\.degruyter\.com\/.+\/[0-9]+'
    LINK_STRINGS = {
        'https://www.degruyter.com/downloadepub/title/{}': {
            'flags': {
                'local': False,
                'download': True,
                'ebook': True,
                'images': True
            },
            'media_type': 'application/epub+zip'
        },
        'https://www.degruyter.com/downloadpdf/title/{}': {
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
            return True
        
        return False
    
    def createLinks(self):
        links = []

        isbnMatch = re.search(r'(978[0-9]+)', self.uri)
        if isbnMatch is not None:
            degISBN = isbnMatch.group(1)
            redirectURL = 'https://www.degruyter.com/view/books/{}/{}/{}.xml'.format(
                *[degISBN] * 3
            )
        else:
            redirectURL = 'https://{}'.format(self.uri)

        redirectHead = requests.head(
            redirectURL,
            allow_redirects=False,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)'}
        )
        if redirectHead.status_code == 301:
            degruPageLocation = redirectHead.headers['Location']
            idMatch = re.search(r'\/title\/([0-9]+)(?:$|\?)', degruPageLocation)
            if idMatch is not None:
                self.identifier = idMatch.group(1)

                for urlStr, attrs in self.LINK_STRINGS.items():
                    outFile = None
                    if 'epub' in urlStr:
                        outFile = 'degruyter_{}.epub'.format(self.identifier)
                        epubURL = urlStr.format(self.identifier)
                        epubHeader = requests.head(
                            epubURL,
                            allow_redirects=False,
                            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)'}
                        )
                        if epubHeader.status_code != 200:
                            continue
                    links.append((
                        urlStr.format(self.identifier),
                        attrs['flags'],
                        attrs['media_type'],
                        outFile
                    ))
        
        return links
