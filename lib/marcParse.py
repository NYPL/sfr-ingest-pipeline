import re
import pycountry
import requests
from requests.exceptions import ConnectionError, MissingSchema, InvalidURL

from helpers.errorHelpers import MARCXMLError, DataError
from helpers.logHelpers import createLog

from lib.dataModel import (
    WorkRecord,
    Identifier,
    Subject,
    Language,
    InstanceRecord,
    Date,
    Agent,
    Format,
    Rights,
    Link
)

logger = createLog('marc_parser')

SUBJECT_INDICATORS = {
    '0': 'lcsh',
    '1': 'lcch',
    '2': 'msh',
    '3': 'nalsaf',
    '4': None,
    '5': 'csh',
    '6': 'rvm',
}


def parseMARC(records, marcRels):
    """Accepts list of MARCXML records and invokes the parser for each. If
    an error occurs None is returned and filter() removes them from the list
    """
    logger.info('Transforming MARCXML records into SFR objects')
    return list(filter(None, (transformMARC(r, marcRels) for r in records)))


def transformMARC(record, marcRels):
    """Accepts a marcalyx object and transforms the MARC record into a SFR
    data object.
    """
    doabID = record[0]
    dateIssued = record[1]
    marcRecord = record[2]
    logger.info('Transforming record {} into a SFR object'.format(doabID))

    work = WorkRecord()
    instance = InstanceRecord()
    item = Format(source='doab', contentType='ebook')

    # Add issued date to work record
    work.addClassItem('dates', Date, **{
        'display_date': dateIssued,
        'date_range': dateIssued,
        'date_type': 'issued'
    })

    # All DOAB records have the same CreativeCommons license, assign this
    # to Instance/Item records
    rights = Rights(
        source='doab',
        license='https://creativecommons.org/licenses/by-nc-nd/4.0/',
        statement='Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International'
    )
    instance.rights.append(rights)
    item.rights.append(rights)

    # A single DOAB identifier can be assigned to the work/instance/item records
    doabIdentifier = Identifier(
        type='doab',
        identifier=doabID,
        weight=1
    )
    work.identifiers.append(doabIdentifier)
    instance.identifiers.append(doabIdentifier)
    item.identifiers.append(doabIdentifier)

    # Code Fields (Identifiers)
    logger.debug('Parsing 0X0-0XX Fields')
    controlData = [
        ('010', 'identifiers', 'a', 'lccn'),
        ('020', 'identifiers', 'a', 'isbn'),
        ('022', 'identifiers', 'a', 'issn'),
        ('050', 'identifiers', 'a', 'lcc'),
        ('082', 'identifiers', 'a', 'ddc'),
        ('010', 'identifiers', 'z', 'lccn'),
        ('020', 'identifiers', 'z', 'isbn'),
        ('022', 'identifiers', 'z', 'issn'),
        ('050', 'identifiers', 'z', 'lcc'),
        ('082', 'identifiers', 'z', 'ddc')
    ]
    for field in controlData:
        extractSubfieldValue(marcRecord, work, field)
        extractSubfieldValue(marcRecord, instance, field)

    # Author/Creator Fields
    logger.debug('Parsing 100, 110 & 111 Fields')
    agentData = ['100', '110', '111', '700', '710', '711']
    for agentField in agentData:
        extractAgentValue(marcRecord, work, agentField, marcRels)

    # Title Fields
    logger.debug('Parsing 21X-24X Fields')
    titleData = [
        ('210', 'alt_titles', 'a'),
        ('222', 'alt_titles', 'a'),
        ('242', 'alt_titles', 'a'),
        ('246', 'alt_titles', 'a'),
        ('247', 'alt_titles', 'a'),
        ('245', 'title', 'a'),
        ('245', 'sub_title', 'b')
    ]
    for field in titleData:
        extractSubfieldValue(marcRecord, work, field)
        extractSubfieldValue(marcRecord, instance, field)

    # Edition Fields
    logger.debug('Parsing Edition (250 & 260) Fields')
    editionData = [
        ('250', 'edition_statement', 'a'),
        ('250', 'edition_statement', 'b'),
        ('260', 'pub_place', 'a'),
        ('260', 'pub_date', 'c'),
        ('260', 'agents', 'b', 'publisher'),
        ('260', 'agents', 'f', 'manufacturer'),
        ('264', 'copyright_date', 'c')
    ]
    for field in editionData:
        extractSubfieldValue(marcRecord, instance, field)

    # Physical Details
    # TODO Load fields into items/measurements?
    logger.debug('Parsing Extent (300) Field')
    extentData = [
        ('300', 'extent', 'a'),
        ('300', 'extent', 'b'),
        ('300', 'extent', 'c'),
        ('300', 'extent', 'e'),
        ('300', 'extent', 'f')
    ]
    for field in extentData:
        extractSubfieldValue(marcRecord, instance, field)

    # Series Details
    logger.debug('Parsing Series (490) Field')
    seriesData = [
        ('490', 'series', 'a'),
        ('490', 'series_position', 'v')
    ]
    for field in seriesData:
        extractSubfieldValue(marcRecord, work, field)

    # Notes/Description details
    # TODO What fields should we bring in?
    logger.debug('Parsing TOC (505) Field')
    tocData = [
        ('505', 'table_of_contents', 'a'),
        ('520', 'summary', 'a')
    ]
    for field in tocData:
        extractSubfieldValue(marcRecord, instance, field)

    # Language Fields
    if len(marcRecord['546']) > 0:
        for lang in marcRecord['546'][0].subfield('a'):
            langs = re.split(r'/|\|', lang.value)
            for language in langs:
                logger.debug('Adding language {} to work and instance'.format(language))
                langObj = pycountry.languages.get(name=language.strip())
                if langObj is None or langObj.alpha_3 == 'und':
                    logger.warning('Unable to parse language {}'.format(language))
                    continue
                sfrLang = Language(
                    language=language,
                    iso2=langObj.alpha_2,
                    iso3=langObj.alpha_3
                )
                work.language.append(sfrLang)
                instance.language.append(sfrLang)

    # Subject Details
    logger.debug('Parsing 6XX Subject Fields')
    subjectData = ['600', '610', '648', '650', '651', '655', '656', '657']
    for subjectType in subjectData:
        extractSubjects(marcRecord, work, subjectType)

    # Eletronic Holding Details
    logger.debug('Parsing 856 (Electronic Holding) Field')
    extractHoldingsLinks(marcRecord['856'], instance, item)

    # TODO Load data for these fields
    # 76X-78X
    # 80X-83X
    instance.formats.append(item)
    work.instances.append(instance)
    return work


def extractAgentValue(data, rec, field, marcRels):
    """Extract's agent names and roles from the relevant MARC fields and appends
    SFR Agent objects to the current record.
    """
    for agentField in data[field]:
        if len(agentField['a']) == 0: continue
        agent = Agent(role=[])
        agent.name = agentField['a'][0].value
        roleCode = agentField['4'][0].value if len(agentField['4']) > 0 else 'aut'
        agent.roles.append(marcRels[roleCode])
        rec.agents.append(agent)


def extractHoldingsLinks(holdings, instance, item):
    """Extracts holdings data from MARC and adds it to the current SFR object
    as links.
    """
    itemURIs = set()
    for holding in holdings:
        if holding.ind1 != '4':
            continue
        try:
            uri = holding.subfield('u')[0].value
            itemURIs.add(parseHoldingURI(uri))
        except (IndexError, DataError):
            logger.info('Could not load URI {} for instance, skipping'.format(holding))
            continue
    
    for itemURI in itemURIs:
        uriFlags = {
            'local': False,
            'download': True,
            'images': True,
            'ebook': True
        }
        if 'text/html' in itemURI[1]:
            logger.info('Adding Read Online link {} for item record'.format(uri))
            uriFlags['download'] = False
            item.addClassItem('links', Link, **{
                'url': itemURI[0],
                'media_type': itemURI[1],
                'flags': uriFlags
            })
        else:         
            logger.info('Adding Download link {} for item record'.format(uri))
            item.addClassItem('links', Link, **{
                'url': itemURI[0],
                'media_type': itemURI[1],
                'flags': uriFlags
            })


def parseHoldingURI(uri):
    logger.info('Loading URI {}'.format(uri))
    try:
        uriHead = requests.head(uri, allow_redirects=False)
        headers = uriHead.headers
    except (MissingSchema, ConnectionError, InvalidURL):
        raise DataError('Invalid Holding URL')

    if uriHead.status_code in [301, 302, 307, 308]:
        redirectTo = headers['Location']
        logger.debug('Found {} Redirect to {}'.format(
            uriHead.status_code,
            redirectTo
        ))
        return parseHoldingURI(redirectTo)
    
    try:
        contentType = headers['Content-Type']
    except KeyError:
        logger.warning('Unable to find header Content-Type for {}'.format(uri))
        contentType = 'text/html'
    
    return uri, contentType
    

def extractSubjects(data, rec, field):
    """Extracts subject fields from the MARC record and assigns them to the 
    current SFR Work record.
    """
    subjectFields = ['a']
    for subj in data[field]:
        subject = {
            'subject': [],
            'subdivision': [],
            'authority': None,
            'uri': None
        }

        # Extract subject text from MARC, will add additional fields as it
        # becomes necessary
        if field == '600':
            subjectFields.extend(['b', 'c', 'd', 'q'])
        elif field == '610' or field == '650':
            subjectFields.extend(['b', 'c', 'd'])
        elif field == '655':
            subjectFields.extend(['b', 'c'])

        for field in subjectFields:
            try:
                subject['subject'].append(subj.subfield(field)[0].value)
            except IndexError:
                pass

        for subfield in ['v', 'x', 'y', 'z']:
            try:
                subject['subdivision'].append(subj.subfield(subfield)[0].value)
            except IndexError:
                pass

        if subj.ind2 != '7':
            try:
                subject['authority'] = SUBJECT_INDICATORS[subj.ind2]
            except KeyError as err:
                logger.error('Unknown subject authority found for {}'.format(subject['authority']))
                logger.debug(err)
        else:
            try:
                subject['authority'] = subj.subfield('2')[0].value
            except IndexError:
                pass

        try:
            subject['uri'] = subj.subfield('0')[0].value
        except IndexError:
            pass

        subjectText = ', '.join(subject['subject'])
        if len(subject['subdivision']) > 0:
            subjectText = '{} -- {}'.format(
                subjectText,
                ' -- '.join(subject['subdivision'])
            )

        rec.addClassItem('subjects', Subject, **{
            'authority': subject['authority'],
            'uri': subject['uri'],
            'subject': subjectText
        })


def extractSubfieldValue(data, record, fieldData):
    """A generic parser for MARC fields. Accepts the current record and a tuple
    of field data which contains:
    field: The MARC field number (e.g. 100, 245, etc.)
    attr: The attribute of the supplied SFR record to assign data to
    subfield: The subfield code from which to extract data (e.g. a, z, 4)
    """
    field = fieldData[0]
    attr = fieldData[1]
    subfield = fieldData[2]
    try:
        for fieldInstance in data[field]:
            fieldValue = fieldInstance.subfield(subfield)[0].value
            if attr == 'agents':
                role = fieldData[3]
                record.agents.append(Agent(
                    name=fieldValue,
                    role=role
                ))
            elif attr == 'identifiers':
                controlField = fieldData[3]
                record.addClassItem('identifiers', Identifier, **{
                    'type': controlField,
                    'identifier': fieldValue.strip(),
                    'weight': 1
                })
            elif attr in ['pub_date', 'copyright_date']:
                record.addClassItem('dates', Date, **{
                    'display_date': fieldValue,
                    'date_range': fieldValue,
                    'date_type': attr
                })
            else:
                if record[attr] is None:
                    record[attr] = fieldValue
                elif type(record[attr]) is list:
                    record[attr].append(fieldValue)
                elif type(record[attr]) is str:
                    record[attr] += '; {}'.format(fieldValue)
    except IndexError as err:
        logger.error('Could not load subfield {} for field {}'.format(
            subfield,
            field
        ))
        logger.debug(err)