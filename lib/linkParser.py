from lib.dataModel import Link

from lib.parsers.defaultParser import DefaultParser
from lib.parsers.frontierParser import FrontierParser

class LinkParser:
    PARSERS = [
        FrontierParser,
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



