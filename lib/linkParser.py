from lib.dataModel import Link, Identifier

from lib.parsers.defaultParser import DefaultParser
from lib.parsers.frontierParser import FrontierParser
from lib.parsers.springerParser import SpringerParser

class LinkParser:
    PARSERS = [
        FrontierParser,
        SpringerParser,
        DefaultParser
    ]
    def __init__(self, item, uri, media_type):
        self.item = item
        self.uri = uri
        self.media_type = media_type
    
    def selectParser(self):
        for model in self.PARSERS:
            parser = model(self.uri, self.media_type)
            if parser.validateURI() is True:
                self.parser = parser
                break

    def createLinks(self):
        for link in self.parser.createLinks():
            self.item.addClassItem('links', Link, **{
                'url': link[0],
                'media_type': link[2],
                'flags': link[1] 
            })

            if link[3] is not None:
                setattr(self.item, 'fileName', link[3])
                self.item.addClassItem('identifiers', Identifier, **{
                    'type': 'doab',
                    'identifier': link[3],
                    'weight': 1
                })



