class DefaultParser:
    def __init__(self, uri, media_type):
        self.uri = uri
        self.media_type = media_type
    
    def validateURI(self):
        return True  # The "base" case that accepts all links
    
    def createLinks(self):
        flags = {
            'local': False,
            'download': False,
            'ebook': True,
            'images': True
        }
        if 'text/html' not in self.media_type:
            flags['download'] = True

        return [(self.uri, flags, self.media_type)]