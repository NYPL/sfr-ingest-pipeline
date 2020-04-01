from abc import ABC, abstractmethod


class AbsSourceReader(ABC):
    """Abstract fetcher for ebook sources from publishers and other small projects"""
    @abstractmethod
    def collectResourceURLs(self):
        """Collect a set of URLs from the index of a source

        Arguments:
            indexURL {string} -- Base URL for the index of the source

        Returns:
            [list] -- List of individual resource pages
        """
        return None

    @abstractmethod
    def scrapeResourcePages(self):
        """Iterate through the collected pages and invoke the scraper on each"""
        return None

    @abstractmethod
    def scrapeRecordMetadata(self):
        """Parses individual page for record metadata

        Returns:
            [dict] -- Scraped metadata
        """
        return 'abstractReader'

    @abstractmethod
    def transformMetadata(self):
        """Accept scraped metadata and transform it into the SFR data model
        """
        return None
