class SFRCover:
    """Simple object that represents a cover image. The URI is the original URI
    from the provider identified by the source.
    """
    def __init__(self, uri, source, mediaType, instanceID):
        """Initialize a cover object

        Arguments:
            uri {string} -- URI to the providers copy of the cover image
            source {string} -- Source of the cover image
            instanceID {integer} -- Unique identifier to db record for instance
        """
        self.uri = uri
        self.source = source
        self.mediaType = mediaType
        self.instanceID = instanceID

    def __repr__(self):
        return '<Cover(uri={}, source={})>'.format(self.uri, self.source)
