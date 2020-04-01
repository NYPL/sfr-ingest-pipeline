import inspect

from lib.dataModel import Link, Identifier
import lib.parsers as parsers


class LinkParser:
    def __init__(self, item, uri, media_type):
        self.item = item
        self.uri = uri
        self.media_type = media_type
        self.parsers = inspect.getmembers(parsers, inspect.isclass)
    
    def selectParser(self):
        sortedParsers = self.sortParsers()
        for model in sortedParsers:
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

    def sortParsers(self):
        parserList = []
        for parser in self.parsers:
            _, parserClass = parser
            parserList.append(parserClass)
        return sorted(parserList, key=lambda x: x.ORDER)
        

