from lxml import etree

from helpers.logHelpers import createLog
from helpers.errorHelpers import ProcessingError

logger = createLog('country_code_generator')


def loadCountryCodes():
    """HathiTrust records include publication places encoded in the MARC
    country code format. These codes are accessed via an XML file from LOC that
    provides the full-text versions of these country names. This function
    generates a dict that correlates these codes with the full-text values,
    which is used to translate the codes for use in SFR
    """

    logger.info('Parsing country code/names dict from local file')

    try:
        countryXML = open('lib/marc_countries.xml')
    except FileNotFoundError:
        logger.error('Could find file at path {}'.format(
            'lib/marc_countries.xml'
        ))
        raise ProcessingError(
            'loadCountryCodes',
            'Could not open marc_countries.xml'
        )

    with countryXML as countryXML:
        countryTree = etree.parse(countryXML)
        codeList = countryTree.getroot()

        logger.info('Retrieving country names from lib/marc_countries.xml')
        ns = '{info:lc/xmlns/codelist-v1}'
        return dict([
            (
                c.find('{}code'.format(ns)).text,
                c.find('{}name'.format(ns)).text
            )
            for c in codeList.findall('.//{}country'.format(ns))
        ])
