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

    countryTrans = {}

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
        countries = codeList.find('{info:lc/xmlns/codelist-v1}countries')
        for country in countries.findall('{info:lc/xmlns/codelist-v1}country'):
            code = None
            name = None
            for child in country:
                if child.tag == '{info:lc/xmlns/codelist-v1}code':
                    code = child.text
                elif child.tag == '{info:lc/xmlns/codelist-v1}name':
                    name = child.text
            logger.debug('Extracted country {} for code {}'.format(name, code))
            countryTrans[code] = name

    logger.info('Retrieved country names from lib/marc_countries.xml')

    return countryTrans
