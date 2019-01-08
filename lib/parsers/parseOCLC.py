import re
from datetime import datetime

from helpers.logHelpers import createLog
from lib.dataModel import InstanceRecord, Agent, Link, Identifier

logger = createLog('classify_parse')

MEASUREMENT_TIME = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

SUBJECT_INDICATORS = {
    '0': 'lcsh',
    '1': 'lcch',
    '2': 'msh',
    '3': 'nalsaf',
    '4': None,
    '5': 'csh',
    '6': 'rvm',
}


def readFromMARC(marcRecord):
    """Parse marcalyx Record object representing oclc record"""
    logger.debug('Parsing Returned Edition')

    instance = InstanceRecord()

    # Control Fields
    oclcNumber = marcRecord['001'][0].value
    instance.addIdentifier(**{
        'type': 'oclc',
        'identifier': oclcNumber,
        'weight': 1
    })

    generalInfo = marcRecord['008'][0].value
    instance.language = generalInfo[35:38]
    print(instance.language)

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
        extractSubfieldValue(marcRecord, instance, field)

    # Language Fields
    if len(marcRecord['041']) > 0:
        for lang in marcRecord['041'][0].subfield('a'):
            if instance.language is None:
                instance.language = lang.value
            else:
                instance.language += ';{}'.format(lang.value)

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
        extractSubfieldValue(marcRecord, instance, field)

    # Notes/Description details
    # TODO What fields should we bring in?
    logger.debug('Parsing TOC (505) Field')
    tocData = [
        ('505', 'table_of_contents', 'a')
    ]
    for field in tocData:
        extractSubfieldValue(marcRecord, instance, field)

    # Subject Details
    logger.debug('Parsing 6XX Subject Fields')
    subjectData = ['600', '610', '648', '650', '651', '655', '656', '657']
    for subjectType in subjectData:
        extractSubjects(marcRecord, instance, subjectType)

    # Eletronic Holding Details
    logger.debug('Parsing 856 (Electronic Holding) Field')
    extractHoldingsLinks(marcRecord['856'], instance)

    # TODO Load data for these fields
    # 100/110/111
    # 70X-75X
    # 76X-78X
    # 80X-83X

    return instance


def extractHoldingsLinks(holdings, instance):
    for holding in holdings:
        if holding.ind1 != '4':
            continue
        try:
            uri = holding.subfield('u')[0].value
        except IndexError:
            logger.info('Could not load URI for identifier, skipping')
            continue


        uriIdentifier = re.search(r'\/((?:(?!\/).)+)$', uri).group(1)

        try:
            holdingFormat = holding.subfield('q')[0].value
            if 'epub' in holdingFormat.lower():
                logger.info('Adding format for instance record for {}'.format(uri))
                instance.addFormat(**{
                    'content_type': holdingFormat,
                    'link': Link(url=uri, mediaType='text/html'),
                    'identifier': Identifier(identifier=uriIdentifier)
                })
                continue
        except IndexError:
            pass

        try:
            note = holding.subfield('z')[0].value
            if 'epub' in note.lower() or 'ebook' in note.lower():
                logger.info('Adding format for instance record for {}'.format(uri))
                instance.addFormat(**{
                    'content_type': 'ebook',
                    'link': Link(url=uri, mediaType='text/html'),
                    'identifier': Identifier(identifier=uriIdentifier)
                })
                continue
        except IndexError:
            pass

        logger.info('Adding link relationship for {}'.format(uri))
        instance.addLink(**{
            'url': uri,
            'media_type': 'text/html',
            'rel_type': 'associated'
        })


def extractSubjects(data, instance, field):
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
            subject['authority'] = SUBJECT_INDICATORS[subj.ind2]
        else:
            subject['authority'] = subj.subfield('2')[0].value

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

        instance.addSubject(**{
            'authority': subject['authority'],
            'uri': subject['uri'],
            'subject': subjectText
        })


def extractSubfieldValue(data, record, fieldData):
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
                record.addIdentifier(**{
                    'type': controlField,
                    'identifier': fieldValue.strip(),
                    'weight': 1
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
