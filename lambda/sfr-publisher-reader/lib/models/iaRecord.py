from datetime import datetime
import pycountry
import requests
from urllib.parse import quote_plus

from ..dataModel import (
    WorkRecord, InstanceRecord, Format, Identifier, Language, Agent, Subject,
    Link, Date, Rights
)
from helpers.logHelpers import createLog

logger = createLog('iaItem')


class IAItem(object):
    ROOT_URL = 'https://archive.org/{}/{}/{}'
    SFR_CROSSWALK = {
        'title': [
            {'level': 'work', 'field': 'title'},
            {'level': 'instance', 'field': 'title'},
        ],
        'creator': [{'level': 'work', 'field': 'author'}],
        'subject': [{'level': 'work', 'field': 'subjects'}],
        'publisher': [{'level': 'instance', 'field': 'publisher'}],
        'date': [{'level': 'instance', 'field': 'publication_date'}],
        'contributor': [{'level': 'item', 'field': 'provider'}],
        'sponsor': [{'level': 'item', 'field': 'sponsor'}],
        'description': [{'level': 'instance', 'field': 'summary'}],
        'edition': [{'level': 'instance', 'field': 'edition_statement'}],
        'language': [
            {'level': 'work', 'field': 'language'},
            {'level': 'instance', 'field': 'language'}
        ],
        'possible-copyright-status': [
            {'level': 'instance', 'field': 'rights_reason'},
            {'level': 'item', 'field': 'rights_reason'}
        ],
        'oclc-id': [
            {'level': 'work', 'field': 'identifier.oclc'},
            {'level': 'instance', 'field': 'identifier.oclc'},
            {'level': 'item', 'field': 'identifier.oclc'}
        ],
        'external-identfier': [
            {'level': 'work', 'field': 'identifier.mixed'},
            {'level': 'instance', 'field': 'identifier.mixed'},
            {'level': 'item', 'field': 'identifier.mixed'}
        ],
        'isbn': [
            {'level': 'work', 'field': 'identifier.isbn'},
            {'level': 'instance', 'field': 'identifier.isbn'},
            {'level': 'item', 'field': 'identifier.isbn'}
        ],
        'lccn': [
            {'level': 'work', 'field': 'identifier.lccn'},
            {'level': 'instance', 'field': 'identifier.lccn'},
            {'level': 'item', 'field': 'identifier.lccn'}
        ],
        'identifier-access': [{'level': 'item', 'field': 'links'}]
    }

    VIAF_ROOT = 'https://dev-platform.nypl.org/api/v0.1/research-now/viaf-lookup?queryName={}'
    CORPORATE_ROLES = [
        'publisher', 'manufacturer', 'repository', 'digitizer',
        'responsible_organization', 'provider', 'sponsor'
    ]
    def __init__(self, itemID, itemData):
        self.itemID = itemID
        self.data = itemData
        self.work = WorkRecord()
        self.instance = InstanceRecord()
        self.item = Format(
            source='internetarchive',
            contentType='ebook',
            modified=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

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
                sourceValue = self.data.get(key, None)

                # If value set for this field, add to the record
                if sourceValue:
                    logger.debug('Adding {} to {} on {}'.format(
                        sourceValue, field['field'], rec
                    ))
                    rec[field['field']] = sourceValue

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
                Identifier(
                    type=None,
                    identifier='ia.{}'.format(self.itemID),
                    weight=1
                )
            )
            # Extracts identifier fields by prefix
            ids = list(filter(lambda x: x[:11] == 'identifier.', rec.keys()))

            for iden in ids:
                # Extracts spedific identifier type
                idType = iden.split('.')[1]
                if isinstance(rec[iden], str):
                    values = [rec[iden]]
                else:
                    values = rec[iden]

                for value in values:
                    identifier = value if idType != 'generic' else 'ia.{}'.format(value)

                    if idType == 'mixed':
                        _, idType, _, identifier = tuple(value.split(':'))

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
        if isinstance(self.work.subjects, str):
            self.work.subjects = [self.work.subjects]
        self.work.subjects = [
            Subject(subjectType='', value=subj.strip(), weight=1)
            for subj in self.work.subjects
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
        for role in ['sponsor', 'provider']:
            self.parseAgent('item', role)

    def splitPublisherField(self):
        """The 'publisher' field in the IA record corresponds to a MARC 260 field,
        specifically subfields $a and $b, so must be split to extract the
        relevant fields.
        """
        pubField = getattr(self.instance, 'publisher', None)
        if pubField is None:
            return None
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
                try:
                    del self.instance['publisher']
                except KeyError:
                    pass

    def parseAgent(self, rec, role):
        """Parse individual agent record, skipping if none is found
        
        Arguments:
            rec {object} -- Work/Instance/Item record to attach agent to
            role {str} -- Specific role of agent being parsed
        """
        inst = getattr(self, rec)

        try:
            if isinstance(inst[role], str):
                inst[role] = [inst[role]]
        except KeyError:
            logger.warning('No agent with role {} found for record'.format(
                role
            ))
            return None
        
        for agentStr in inst[role]:
            agentRecs = agentStr.split('; ')
            for agentRec in agentRecs:
                logger.debug('Adding {} {} to {}'.format(
                    role, agentRec, inst 
                ))

                newAgent = Agent(name=agentRec.strip(), role=role)

                # Fetch VIAF/LCNAF identifiers for agent
                corporate = True if role != 'author' else False
                self.getVIAF(newAgent, corporate=corporate)

                inst.agents.append(newAgent)

        del inst[role]

    def parseRights(self):
        """Create rights statement for Instance and Item records
        """
        logger.info('Extracting rights metadata')
        for rec in [self.instance, self.item]:
            rights = Rights(
                source='internetarchive',
                license='uncertain',
                statement='Refer to Material for Copyright',
                reason=getattr(rec, 'rights_reason', None)
            )
            rec.rights.append(rights)

            try:
                del rec['rights_reason']
            except KeyError:
                pass

    def parseLanguages(self):
        """Extract language and determine standard ISO codes
        """
        logger.info('Extracting language metadata')
        for rec in [self.work, self.instance]:
            language = getattr(rec, 'language', '')
            if isinstance(language, str):
                language = [language]

            parsedLangs = []
            for lang in language:
                # Parses language to find ISO codes
                langObj = pycountry.languages.get(alpha_3=lang.lower())
                if langObj is None or langObj.alpha_3 == 'und':
                    logger.warning(
                        'Language could not be determined for {}'.format(
                            language
                        )
                    )
                    rec.language = []
                    continue

                sfrLang = Language(
                    language=langObj.name,
                    iso_2=langObj.alpha_2,
                    iso_3=langObj.alpha_3
                )
                parsedLangs.append(sfrLang)

            rec.language = parsedLangs
    
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

    def parseSummary(self):
        if isinstance(self.instance.summary, list):
            self.instance.summary = '; '.join(self.instance.summary)

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
        
        # Adding Download PDF Link
        downloadLink = Link(
            url=self.ROOT_URL.format(
                'download',
                self.itemID,
                '{}.pdf'.format(self.itemID)
            ),
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
                url=self.ROOT_URL.format('services', 'img', self.itemID),
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
