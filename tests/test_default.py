import unittest


from lib.parsers.defaultParser import DefaultParser

class TestDefaultParser(unittest.TestCase):
    def test_init(self):
        defaultTest = DefaultParser('uri', 'type')
        self.assertEqual(defaultTest.uri, 'uri')
        self.assertEqual(defaultTest.media_type, 'type')
    
    def test_validateURI(self):
        defaultTest = DefaultParser('uri', 'type')
        self.assertTrue(defaultTest.validateURI())

    def test_createLinks_no_download(self):
        defaultTest = DefaultParser('uri', 'text/html')
        testLink = defaultTest.createLinks()
        self.assertEqual(testLink[0][0], 'uri')
        self.assertFalse(testLink[0][1]['download'])
        self.assertEqual(testLink[0][2], 'text/html')

    def test_createLinks_download(self):
        defaultTest = DefaultParser('uri', 'type')
        testLink = defaultTest.createLinks()
        self.assertEqual(testLink[0][0], 'uri')
        self.assertTrue(testLink[0][1]['download'])
        self.assertEqual(testLink[0][2], 'type')
