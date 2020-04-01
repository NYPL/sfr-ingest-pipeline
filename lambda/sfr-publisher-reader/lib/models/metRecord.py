from datetime import datetime
import pycountry
import requests
from urllib.parse import quote_plus

from ..dataModel import (
    WorkRecord, InstanceRecord, Format, Identifier, Language, Agent, Subject,
    Link, Date, Rights
)
from helpers.logHelpers import createLog

logger = createLog('metItem')


class MetItem(object):
    ROOT_URL = 'https://libmma.contentdm.oclc.org/digital'
    ITEM_UI = 'https://libmma.contentdm.oclc.org/digital/collection/p15324coll10/id/{}/rec/1'
    SFR_CROSSWALK = {
        'title': [
            {'level': 'work', 'field': 'title'},
            {'level': 'instance', 'field': 'title'},
        ],
        'creato': [{'level': 'work', 'field': 'author'}],
        'descri': [{'level': 'instance', 'field': 'summary'}],
        'subjec': [{'level': 'work', 'field': 'subjects'}],
        'publis': [{'level': 'instance', 'field': 'publisher'}],
        'date': [{'level': 'instance', 'field': 'publication_date'}],
        'format': [{'level': 'instance', 'field': 'format'}],
        'physic': [{'level': 'item', 'field': 'repository'}],
        'source': [{'level': 'item', 'field': 'provider'}],
        'langua': [
            {'level': 'work', 'field': 'language'},
            {'level': 'instance', 'field': 'language'}
        ],
        'rights': [
            {'level': 'instance', 'field': 'license'},
            {'level': 'item', 'field': 'license'}
        ],
        'copyra': [
            {'level': 'instance', 'field': 'rights_statement'},
            {'level': 'item', 'field': 'rights_statement'}
        ],
        'copyri': [
            {'level': 'instance', 'field': 'rights_reason'},
            {'level': 'item', 'field': 'rights_reason'}
        ],
        'digiti': [
            {'level': 'work', 'field': 'identifier.generic'},
            {'level': 'instance', 'field': 'identifier.generic'},
            {'level': 'item', 'field': 'identifier.generic'}
        ],
        'dmoclcno': [
            {'level': 'work', 'field': 'identifier.oclc'},
            {'level': 'instance', 'field': 'identifier.oclc'},
            {'level': 'item', 'field': 'identifier.oclc'}
        ],
        'link': [{'level': 'item', 'field': 'links'}]
    }

    VIAF_ROOT = 'https://dev-platform.nypl.org/api/v0.1/research-now/viaf-lookup?queryName={}'
    CORPORATE_ROLES = [
        'publisher', 'manufacturer', 'repository', 'digitizer',
        'responsible_organization'
    ]
    def __init__(self, itemID, itemData):
        self.itemID = itemID
        self.data = itemData
        self.work = WorkRecord()
        self.instance = InstanceRecord()
        self.item = Format(
            source='met',
            contentType='ebook',
            modified=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    def extractRelevantData(self):
        logger.debug('Extracting array of metadata fields')

        # If this is a collection the parent object will contain the metadata
        # otherwise it is found in the root object
        if 'parent' in self.data.keys() and self.data['parent'] is not None:
            self.fields = self.transformFields(self.data['parent']['fields'])
        else:
            self.fields = self.transformFields(self.data['fields'])
        
        # Links to various associated resources are stored as relative paths
        # These will be used later
        try:
            self.downloadURI = self.data['downloadParentUri'].replace('/digital', '')
        except (KeyError, AttributeError):
            self.downloadURI = self.data['downloadUri']
        self.coverURI = self.data['imageUri']
        self.viewURI = self.ITEM_UI.format(self.itemID)
    
    def transformFields(self, fields):
        """Transforms the array of metadata fields into a dict, where the 
        key attribute of the object in the array is the dict's key
        
        Arguments:
            fields {list} -- List of metadata elements
        
        Returns:
            [dict] -- Object containing transposed metadata fields
        """
        return {f['key']: f for f in fields}

    def createStructure(self):
        """Takes the set of relevant fields as defined in the in the mapping
        in this class and uses these to extract metadata from the MET source
        object.
        """
        logger.info('Creating basic metadata structure')
        for key, fields in self.SFR_CROSSWALK.items():
            for field in fields:
                # Get relevant work/instance/item record
                rec = getattr(self, field['level'])
                sourceValue = self.fields.get(key, None)

                # If value set for this field, add to the record
                if sourceValue:
                    logger.debug('Adding {} to {} on {}'.format(
                        sourceValue['value'], field['field'], rec
                    ))
                    rec[field['field']] = sourceValue['value']

    def parseIdentifiers(self):
        """Parse identifiers from assigned records into Identifier objects
        """
        logger.info('Extracting identifiers')
        for rec in [self.work, self.instance, self.item]:
            # Append main id from API response
            logger.debug('Adding identifier {}({}) to {}'.format(
                self.itemID, 'generic', rec
            ))
            rec.identifiers.append(
                type=None, identifier='met.{}'.format(self.itemID), weight=1
            )
            # Extracts identifier fields by prefix
            ids = list(filter(lambda x: x[:11] == 'identifier.', rec.keys()))

            for iden in ids:
                # Extracts spedific identifier type
                idType = iden.split('.')[1]
                identifier = rec[iden] if idType != 'generic' else 'met.{}'.format(rec[iden])

                logger.debug('Adding identifier {}({}) to {}'.format(
                    identifier, idType, rec
                ))
                rec.identifiers.append(
                    Identifier(
                        type=idType if idType != 'generic' else None,
                        identifier=identifier,
                        weight=1
                    )
                )
                del rec[iden]

        self.work.primary_identifier = self.work.identifiers[0]

    def parseSubjects(self):
        """Transforms delimited string of subjects into array of Subjects
        attached to the work record
        """
        logger.info('Extracting subjects')
        subjStr = self.work.subjects
        subjs = subjStr.split(';')
        self.work.subjects = [
            Subject(subjectType='lcsh', value=subj.strip(), weight=1)
            for subj in subjs
        ]
    
    def parseAgents(self):
        """Transform specific agent fields into Agent records attached to each
        record
        """
        logger.info('Extracting Agents')
        for role in ['author']:
            self.parseAgent('work', role)
        for role in ['publisher']:
            self.splitPublisherField()
        for role in ['repository', 'provider']:
            self.parseAgent('item', role)

    def splitPublisherField(self):
        """The 'publis' field in the MET record corresponds to a MARC 260 field,
        specifically subfields $a and $b, so must be split to extract the
        relevant fields.
        """
        pubField = self.instance.publisher
        publishers = pubField.split(';')

        for pub in publishers:
            pubData = pub.split(':')
            if self.instance.pub_place is None: # Take first place only
                pubPlace = pubData[0].strip()
                logger.info('Adding {} as publication place'.format(pubPlace))
                self.instance.pub_place = pubPlace

            if len(pubData) > 1:
                publisher = pubData[1].strip()
                self.instance.publisher = publisher
                self.parseAgent('instance', 'publisher')
            else:
                # If no publisher exists we must still remove this field from
                # the record
                del self.instance['publisher']

    def parseAgent(self, rec, role):
        """Parse individual agent record, skipping if none is found
        
        Arguments:
            rec {object} -- Work/Instance/Item record to attach agent to
            role {str} -- Specific role of agent being parsed
        """
        inst = getattr(self, rec)
        try:
            logger.debug('Adding {} {} to {}'.format(
                role, inst[role], inst 
            ))

            newAgent = Agent(name=inst[role], role=role)

            # Fetch VIAF/LCNAF identifiers for agent
            corporate = True if role != 'author' else False
            self.getVIAF(newAgent, corporate=corporate)

            inst.agents.append(newAgent)
            del inst[role]
        except KeyError:
            logger.warning('No agent with role {} found for record'.format(role))
            pass

    def parseRights(self):
        """Create rights statement for Instance and Item records
        """
        logger.info('Extracting rights metadata')
        for rec in [self.instance, self.item]:
            # Transforms the license string into a uniform format
            rightsLicense = getattr(rec, 'license', None).replace(' ', '_').lower()

            # Check to see if this is "copyrighted" which is the METs term for
            # all records they do not release in the public domain. We refer
            # users back to the MET for these records.
            if rightsLicense == 'copyrighted':
                logger.debug('Found uncertain record, adding custom rights')
                rightsLicense = 'uncertain'
                rightsStatement = 'Refer to Material for Copyright'
            else:
                logger.debug('Adding MET assigned rights statement and license')
                rightsStatement = getattr(rec, 'rights_statement', None)

            rights = Rights(
                source='met',
                license=rightsLicense,
                statement=rightsStatement,
                reason=getattr(rec, 'rights_reason', None)
            )
            rec.rights.append(rights)

            # These fields can be safely removed once the rights object exists
            for field in ['license', 'rights_statement', 'rights_reason']:
                del rec[field]

    def parseLanguages(self):
        """Extract language and determine standard ISO codes
        """
        logger.info('Extracting language metadata')
        for rec in [self.work, self.instance]:
            language = getattr(rec, 'language', '')

            # Parses language to find ISO codes
            langObj = pycountry.languages.get(name=language.strip().title())
            if langObj is None or langObj.alpha_3 == 'und':
                logger.warning('Language could not be determined for {}'.format(language))
                rec.language = []
                continue

            sfrLang = Language(
                language=language,
                iso_2=langObj.alpha_2,
                iso_3=langObj.alpha_3
            )
            rec.language = [sfrLang]
    
    def parseDates(self):
        """Parses any date fields. Currently only assigns publication date for
        instance records
        """
        logger.info('Extracting date metadata')
        pubDate = getattr(self.instance, 'publication_date', None)

        if pubDate:
            logger.debug('Adding pub date {} to instance'.format(pubDate))
            newDate = Date(
                displayDate=pubDate,
                dateRange=pubDate,
                dateType='publication_date'
            )
            self.instance.dates.append(newDate)
            del self.instance.publication_date

    def parseLinks(self):
        """Takes previously extracted link formats and assigns them to the Item
        record
        """
        logger.info('Extracting link metadata')

        # Adding View Online Link
        readLink = Link(
            url=self.item.links,
            mediaType='text/html',
            flags={
                'local': False,
                'download': False,
                'ebook': True,
                'images': True
            }
        )
        
        # Adding Download Link
        downloadLink = Link(
            url='{}{}'.format(self.ROOT_URL, self.downloadURI),
            mediaType='application/pdf',
            flags={
                'local': False,
                'download': True,
                'ebook': True,
                'images': True
            }
        )
        self.item.links = [readLink, downloadLink]

    def addCover(self):
        """Adds cover link, which was previously extracted in the same manner
        as the other links. This will be picked up and parsed automatically
        by the ingester for display as a cover
        """
        logger.info('Extracting cover metadata')
        self.instance.links.append(
            Link(
                url='{}{}'.format(self.ROOT_URL, self.coverURI),
                mediaType='image/jpeg',
                flags={'cover': True, 'temporary': True}
            )
        )
    
    def getVIAF(self, agent, corporate=False):
        logger.info('Querying VIAF for {}'.format(agent.name))
        reqStr = self.VIAF_ROOT.format(quote_plus(agent.name))

        if corporate is True:
            reqStr = '{}&queryType=corporate'.format(reqStr)

        viafResp = requests.get(reqStr)
        responseJSON = viafResp.json()
        logger.debug(responseJSON)

        if 'viaf' in responseJSON:
            logger.debug('Found VIAF {} for agent'.format(
                responseJSON.get('viaf', None)
            ))

            if responseJSON['name'] != agent.name:
                if agent.name not in agent.aliases:
                    agent.aliases.append(agent.name)
                agent.name = responseJSON.get('name', '')

            agent.viaf = responseJSON.get('viaf', None)
            agent.lcnaf = responseJSON.get('lcnaf', None)
