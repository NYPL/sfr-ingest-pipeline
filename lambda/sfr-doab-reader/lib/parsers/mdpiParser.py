import re


class MDPIParser:
    ORDER = 4
    REGEX = 'mdpi.com/books/pdfview/book/([0-9]+)$'

    def __init__(self, uri, media_type):
        self.uri = uri
        self.media_type = media_type
    
    def validateURI(self):
        try:
            match = re.search(self.REGEX, self.uri)
            self.identifier = match.group(1)
            return True
        except (IndexError, AttributeError):
            return False

    def createLinks(self):
        return [(
            self.uri.replace('pdfview', 'pdfdownload'),
            {'local': False, 'download': True, 'ebook': True, 'images': True},
            'application/pdf',
            None
        )]
