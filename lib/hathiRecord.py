import re
from datetime import datetime

from lib.hathiCover import HathiCover
from lib.dataModel import (
    WorkRecord,
    Identifier,
    InstanceRecord,
    Format,
    Rights,
    Agent,
    Measurement,
    Date,
    Link
)

from helpers.logHelpers import createLog
from helpers.errorHelpers import DataError

logger = createLog('hathiRecord')


class HathiRecord():
    """Class for constructing HathiTrust-based records in the SFR data model.
    This largely serves as a wrapper for classes imported from the SFR model,
    and includes functions that can build these up. It also contains several
    class-level lookup tables for codes/values provided in the Hathi CSV files.
    """

    # These codes are supplied by Hathi as the determination of an item's
    # rights status.
    rightsReasons = {
        'bib': 'bibliographically-dervied by automatic processes',
        'ncn': 'no printed copyright notice',
        'con': 'contractual agreement with copyright holder on file',
        'ddd': 'due diligence documentation on file',
        'man': 'manual access control override; see note for details',
        'pvt': 'private personal information visible',
        'ren': 'copyright renewal research was conducted',
        'nfi': 'needs further investigation (copyright research partially complete)',
        'cdpp': 'title page or verso contain copyright date and/or place of publication information not in bib record',
        'ipma': 'in-print and market availability research was conducted',
        'unp': 'unpublished work',
        'gfv': 'Google viewability set at VIEW_FULL',
        'crms': 'derived from multiple reviews in the Copyright Review Management System',
        'add': 'author death date research was conducted or notification was received from authoritative source',
        'exp': 'expiration of copyright term for non-US work with corporate author',
        'del': 'deleted from the repository; see not for details',
        'gatt': 'non-US public domain work restroted to in-copyright in the US by GATT',
        'supp': 'suppressed from view; see note for details'
    }

    # Decodes rights statements into full licenses (CreativeCommons links where
    # possible), and human-readable statements.
    rightsValues = {
        'pd': {
            'license': 'public_domain',
            'statement': 'Public Domain'
        },
        'ic': {
            'license': 'in_copyright',
            'statement': 'In Copyright'
        },
        'op': {
            'license': 'in_copyright (out_of_print)',
            'statement': 'Out of Print (implied to be in copyright)'
        },
        'orph': {
            'license': 'in_copyright (orphaned)',
            'statement': 'Copyright Orphaned (implied to be in copyright)'
        },
        'und': {
            'license': 'undetermined',
            'statement': 'Status Undetermined'
        },
        'ic-world': {
            'license': 'in_copyright (viewable)',
            'statement': 'In Copyright, permitted to be world viewable'
        },
        'nobody': {
            'license': 'in_copyright (blocked)',
            'statement': 'Blocked for all users'
        },
        'pdus': {
            'license': 'public_domain (us_only)',
            'statement': 'Public Domain when viewed in the US'
        },
        'cc-by-3.0': {
            'license': 'https://creativecommons.org/licenses/by/3.0/',
            'statement': 'Creative Commons Attribution License, 3.0 Unported'
        },
        'cc-by-nc-3.0': {
            'license': 'https://creativecommons.org/licenses/by-nc-sa/3.0/',
            'statement': 'Creative Commons Attribution, Non-Commercial, 3.0 Unported'
        },
        'cc-by-nc-sa-3.0': {
            'license': 'https://creativecommons.org/licenses/by-nc-sa/3.0/',
            'statement': 'Creative Commons Attribution, Non-Commercial, Share Alike License, 3.0 Unported'
        },
        'cc-by-nd-3.0': {
            'license': 'https://creativecommons.org/licenses/by-nd/3.0/',
            'statement': 'Creative Commons Attribution, No Derivatives License, 3.0 Unported'
        },
        'cc-by-nc-nd-3.0': {
            'license': 'https://creativecommons.org/licenses/by-nc-nd/3.0/',
            'statement': 'Creative Commons Attribution, Non-Commercial, Share Alike License, 3.0 Unported'
        },
        'cc-by-sa-3.0': {
            'license': 'https://creativecommons.org/licenses/by-sa/3.0/',
            'statement': 'Creative Commons Attribution, Share Alike License, 3.0 Unported'
        },
        'orphcand': {
            'license': 'in_copyright (90-day hold)',
            'statement': 'Orphan Candidate - in 90-day holding period'
        },
        'cc-zero': {
            'license': 'https://creativecommons.org/publicdomain/zero/1.0/',
            'statement': 'Creative Commons Universal Public Domain'
        },
        'und-world': {
            'license': 'undetermined',
            'statement': 'Copyright Status undetermined, world viewable'
        },
        'icus': {
            'license': 'in_copyright (in US)',
            'statement': 'In Copyright in the US'
        },
        'cc-by-4.0': {
            'license': 'https://creativecommons.org/licenses/by/4.0/',
            'statement': 'Creative Commons Attribution 4.0 International License'
        },
        'cc-by-nd-4.0': {
            'license': 'https://creativecommons.org/licenses/by-nd/4.0/',
            'statement': 'Creative Commons Attribution, No Derivatives 4.0 International License'
        },
        'cc-by-nc-nd-4.0': {
            'license': 'https://creativecommons.org/licenses/by-nc-nd/4.0/',
            'statement': 'Creative Commons Attribution, Non-Commercial, No Derivatives 4.0 International License'
        },
        'cc-by-nc-4.0': {
            'license': 'https://creativecommons.org/licenses/by-nc/4.0/',
            'statement': 'Creative Commons Attribution, Non-Commercial 4.0 International License'
        },
        'cc-by-nc-sa-4.0': {
            'license': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
            'statement': 'Creative Commons Attribution, Non-Commercial, Share Alike 4.0 International License'
        },
        'cc-by-sa-4.0': {
            'license': 'https://creativecommons.org/licenses/by-sa/4.0/',
            'statement': 'Creative Commons Attribution, Share Alike 4.0 International License'
        },
        'pd-pvt': {
            'license': 'public_domain (privacy_limited)',
            'statement': 'Public Domain access limited for privacy concerns'
        },
        'supp': {
            'license': 'suppressed',
            'statement': 'Suppressed from view'
        }
    }

    # List of institution codes for organizations that have contributed
    # materials to HathiTrust
    sourceCodes = {
        'allegheny': 'Allegheny College',
        'amherst': 'Amherst College',
        'archive': 'Internet Archive',
        'arizona': 'University of Arizona',
        'asu': 'Arizona State University',
        'aub': 'American University of Beirut',
        'auburn': 'Auburn University',
        'auckland': 'University of Auckland',
        'augusta': 'Augusta University',
        'baylor': 'Baylor University',
        'bc': 'Boston College',
        'bently-umich': 'Bentley Historical Library, University of Michigan',
        'berkeley': 'University of California, Berkeley',
        'borndigital': 'Born Digital',
        'brandeis': 'Brandeis University',
        'brooklynmuseum': 'Brooklyn Museum',
        'brown': 'Brown University',
        'brynmawr': 'Bryn Mawr College',
        'bu': 'Boston University',
        'bucknell': 'Bucknell University',
        'buffalo': 'University At Buffalo, The State University of New York',
        'byu': 'Brigham Young University',
        'carleton': 'Carleton College',
        'case': 'Case Western Reserve University',
        'cgu': 'Claremont Graduate University',
        'chtanc': 'National Library of Taiwan',
        'claremont': 'Claremont University Consortium',
        'clark': 'Clark University',
        'clarkart': 'Sterling and Francine Clark Art Institute',
        'clements-umich': 'William L. Clements Library, University of Michigan',
        'clemson': 'Clemson University',
        'cmc': 'Claremont McKenna College',
        'colby': 'Colby College',
        'colorado': 'University of Colorado Boulder',
        'columbia': 'Columbia University',
        'coo': 'Cornell University',
        'cornell': 'Cornell University',
        'dartmouth': 'Dartmouth College',
        'depaul': 'DePaul University',
        'dickinson': 'Dickinson College',
        'duke': 'Duke University',
        'elon': 'Elon University',
        'emory': 'Emory University',
        'fau': 'Florida Atlantic University',
        'fiu': 'Florida International University',
        'flbog': 'State University System of Florida',
        'frick': 'The Frick Collection',
        'fsu': 'Florida State University',
        'gatech': 'Georgia Institute of Technology',
        'gc-cuny': 'CUNY Graduate School and University Center',
        'georgetown': 'Georgetown University',
        'getty': 'The Getty Research Institute',
        'gettyshib': 'Getty Research Institute',
        'gmu': 'George Mason University',
        'grinnell': 'Grinnell College',
        'google': 'Google',
        'gsu': 'Georgia State University',
        'harvard': 'Harvard University',
        'hathitrust': 'HathiTrust',
        'haverford': 'Haverford College',
        'hawaii': 'University of Hawaii',
        'hmc': 'Harvey Mudd College',
        'ht_private': 'Private Donor',
        'ht_support-microsoft': 'Digitization Support from Microsoft',
        'ia': 'Internet Archive',
        'ias': 'IAS, via Princeton University',
        'illinois': 'University of Illinois at Urbana-Champaign',
        'iu': 'Indiana University',
        'jhu': 'Johns Hopkins University',
        'keio': 'Keio University',
        'kennesaw': 'Kennesaw State University',
        'knowledgeunlatched': 'Knowledge Unlatched',
        'ksu': 'Kansas State University',
        'ku': 'University of Kansas',
        'lafayette': 'Lafayette College',
        'lit-dlps-dc': 'University of Michigan Library IT, Digital Library Production Service, Digital Conversion',
        'loc': 'Library of Congress',
        'macalester': 'Macalester College',
        'mcgill': 'McGill University',
        'mcmaster': 'McMaster University',
        'mdanderson': 'University of Texas M.D. Anderson Cancer Center',
        'mdl': 'Minnesota Digital Library',
        'mhs': 'Minnesota Historical Society',
        'miami': 'University of Miami',
        'milproj-dc-umich': 'Millennium Project',
        'missouri': 'University of Missouri-Columbia',
        'mit': 'Massachusetts Institute of Technology',
        'mndigital': 'Minnesota Digital Library',
        'mnhs': 'Minnesota Historical Society',
        'monash': 'Monash University',
        'montana': 'Montana State University',
        'mou': 'University of Missouri',
        'msu': 'Michigan State University',
        'mtholyoke': 'Mount Holyoke College',
        'ncl': 'National Central Library',
        'ncsu': 'North Carolina State University',
        'nd': 'University of Notre Dame',
        'neu': 'Northeastern University',
        'nfb': 'National Federation of the Blind',
        'nmsu': 'New Mexico State University - Las Cruces Campus',
        'nnc': 'Columbia University',
        'northwestern': 'Northwestern University',
        'nypl': 'New York Public Library',
        'nyu': 'New York University',
        'okstate': 'Oklahoma State University',
        'olemiss': 'University of Mississippi',
        'osu': 'The Ohio State University',
        'ou': 'University of Oklahoma',
        'pfw': 'Purdue University Fort Wayne',
        'pitt': 'University of Pittsburgh',
        'pomona': 'Pomona College',
        'press': 'University of Michigan Press',
        'princeton': 'Princeton University',
        'private': 'Private Donor',
        'psu': 'Pennsylvania State University',
        'purdue': 'Purdue University',
        'quensu': 'Queen\'s University',
        'richmond': 'University of Richmond',
        'rochester': 'University of Rochester',
        'rutgers': 'Rutgers University',
        'scripscollege': 'Scripps College',
        'smith': 'Smith College',
        'smu': 'Southern Methodist University',
        'stanford': 'Stanford University',
        'swarthmore': 'Swarthmore College',
        'swmed': 'University of Texas Southwestern Medical Center',
        'syr': 'Syracuse University',
        'tamu': 'Texas A&M',
        'tcu': 'Texas Christian University',
        'technicalreports': 'Technical Report Archive and Image Library',
        'temple': 'Temple University',
        'ttu': 'Texas Tech University',
        'tufts': 'Tufts University',
        'tulane': 'Tulane University',
        'txstate': 'Texas State University - San Marcos',
        'ua': 'University of Alabama',
        'ualberta': 'University of Alberta',
        'ubc': 'University of British Columbia',
        'uc': 'University of Cincinnati',
        'ucalgary': 'University of Calgary',
        'ucdavis': 'University of California, Davis',
        'ucf': 'University of Central Florida',
        'uchicago': 'University of Chicago',
        'uci': 'University of California, Irvine',
        'ucla': 'University of California, Los Angeles',
        'ucm': 'Universidad Complutense de Madrid',
        'ucmerced': 'University of California, Merced',
        'uconn': 'University of Connecticut',
        'ucop': 'University of California, Office of the President',
        'ucr': 'University of California, Riverside',
        'ucsc': 'University of California, Santa Cruz',
        'ucsf': 'University of California, San Francisco',
        'udel': 'University of Delaware',
        'ufl': 'University of Florida',
        'uga': 'University of Georgia',
        'uh': 'University of Houston',
        'uic': 'University of Illinois at Chicago',
        'uiowa': 'University of Iowa',
        'uky': 'University of Kentucky',
        'um-dc-mp': 'University of Michigan, Duderstadt Center, Millennium Project',
        'umass': 'University of Massachusetts',
        'umd': 'University of Maryland',
        'umdl-umich': 'University of Michigan Library IT, Digital Library Production Service, Digital Conversion Unit',
        'umich': 'University of Michigan',
        'umn': 'University of Minnesota',
        'ump': 'University of Michigan Press',
        'unc': 'University of North Carolina',
        'ung': 'University of North Georgia',
        'union': 'Union College',
        'universityofcalifornia': 'University of California',
        'unl': 'University of Nebraska - Lincoln',
        'unlv': 'University of Nevada - Las Vegas',
        'unm': 'University of New Mexico',
        'unr': 'University of Nevada, Reno',
        'uoregon': 'University of Oregon',
        'upenn': 'University of Pennsylvania',
        'uq': 'The University of Queensland',
        'usc': 'University of Southern California',
        'usf': 'University of South Florida',
        'usg': 'University System of Georgia',
        'usu': 'Utah State University',
        'usup': 'Utah State University Press',
        'usupress': 'Utah State University Press',
        'uta': 'University of Texas at Arlington',
        'utah': 'University of Utah',
        'utdallas': 'University of Texas at Dallas',
        'utep': 'University of Texas at El Paso',
        'utexas': 'University of Texas at Austin',
        'uth': 'University of Texas Health Science Center at Houston',
        'utk': 'University of Tennessee, Knoxville',
        'utoronto': 'University of Toronto',
        'utsa': 'University of Texas at San Antonio',
        'uuhhs': 'Unitarian Universalist History and Heritage Society',
        'uvm': 'University of Vermont',
        'uwf': 'University of West Florida',
        'uwyo': 'University of Wyoming',
        'vanderbilt': 'Vanderbilt University',
        'vcu': 'Virginia Commonwealth University',
        'virginia': 'University of Virginia',
        'vt': 'Virginia Tech',
        'washington': 'University of Washington',
        'wau': 'University of Washington',
        'wayne': 'Wayne State University',
        'wesleyan': 'Wesleyan University',
        'wfu': 'Wake Forest University',
        'whitman': 'Whitman College',
        'wichita': 'Wichita State University',
        'williams': 'Williams College',
        'wisc': 'University of Wisconsin',
        'wsu': 'Washington State University',
        'wustl': 'Washington University in St. Louis',
        'wvu': 'West Virginia University',
        'yale': 'Yale University',
        'yale2': 'Yale University'
    }

    identifierFields = [
        ('hathi', 'bib_key'),
        ('hathi', 'htid'),
        (None, 'source_id'),
        ('isbn', 'isbns'),
        ('issn', 'issns'),
        ('lccn', 'lccns'),
        ('oclc', 'oclcs')
    ]

    def __init__(self, ingestRecord, ingestDateTime=None):
        # Initialize with empty SFR data objects
        # self.ingest contains the source data
        self.work = WorkRecord()
        self.ingest = ingestRecord
        self.instance = InstanceRecord()
        self.item = Format()
        self.rights = Rights()
        self.modified = ingestDateTime
        logger.debug('Initializing empty HathiRecord object')

        # We need a fallback modified date if none is provided
        if self.modified is None:
            self.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.debug(
                'Assigning generated timestamp of {} to new record'.format(
                    self.modified
                )
            )
        elif type(self.modified) is datetime:
            self.modified = self.modified.strftime('%Y-%m-%d %H:%M:%S')

    def __repr__(self):
        return '<Hathi(title={})>'.format(self.work.title)

    def buildDataModel(self, countryCodes):
        logger.debug('Generating work record for bib record {}'.format(
            self.ingest['bib_key']
        ))

        # If we don't have a valid rights code, this means that the row has
        # been improperly formatted (generally fields out of order/misplaced)
        # Raise a warning but continue if this is found to be true
        if self.ingest['rights_statement'] not in HathiRecord.rightsReasons:
            raise DataError(
                '{} is malformed (columns missing or incorrect'.format(
                    self.ingest['htid']
                )
            )

        self.buildWork()

        logger.debug('Generating instance record for hathi record {}'.format(
            self.ingest['htid']
        ))
        self.buildInstance(countryCodes)

        logger.debug('Generating an item record for hathi record {}'.format(
            self.ingest['htid']
        ))
        self.buildItem()

        logger.debug('Generate a rights object for the associated rights statement {}'.format(
            self.ingest['rights']
        ))

        # Generate a stand-alone rights object that contains the hathi
        # generated rights information
        self.createRights()

    def buildWork(self):
        """Construct the SFR Work object from the Hathi data"""
        self.work.title = self.ingest['title']

        logger.info('Creating work record for {}'.format(self.work.title))
        # The primary identifier for this work is a HathiTrust bib reference
        self.work.primary_identifier = Identifier(
            type='hathi',
            identifier=self.ingest['bib_key'],
            weight=1
        )
        logger.debug('Setting primary_identifier to {}'.format(
            self.work.primary_identifier
        ))

        for idType, key in HathiRecord.identifierFields:
            logger.debug('Setting identifiers {}'.format(idType))
            self.parseIdentifiers(self.work, idType, key)

        # All government documents should be in the public_domain.
        self.parseGovDoc(self.ingest['gov_doc'], self.ingest['htid'])

        # The copyright date assigned to the work by HathiTrust
        self.work.addClassItem('dates', Date, **{
            'display_date': self.ingest['copyright_date'],
            'date_range': self.ingest['copyright_date'],
            'date_type': 'copyright_date'
        })
        logger.debug('Setting copyright date to {}'.format(
            self.ingest['copyright_date']
        ))

        try:
            self.parseAuthor(self.ingest['author'])
        except KeyError:
            logger.warning('No author associated with record {}'.format(
                self.work
            ))

    def buildInstance(self, countryCodes):
        """Constrict an instance record from the Hathi data provided. As
        structured Hathi trust data will always correspond to a single
        instance. A wok in Hathi can have multiple items, and this relationship
        is reflected in the data.

        We do not attempt to merge records at this phase, but will associated
        works and instances related by identifiers when stored in the database.
        """
        self.instance.title = self.ingest['title']
        self.instance.language = self.ingest['language']
        self.instance.volume = self.ingest['description']

        logger.info('Creating instance record for work {}'.format(self.work))

        self.parsePubPlace(self.ingest['pub_place'], countryCodes)

        for idType, key in HathiRecord.identifierFields:
            logger.debug('Setting identifiers {}'.format(idType))
            self.parseIdentifiers(self.instance, idType, key)

        self.instance.addClassItem('dates', Date, **{
            'display_date': self.ingest['copyright_date'],
            'date_range': self.ingest['copyright_date'],
            'date_type': 'copyright_date'
        })
        logger.debug('Setting copyright date to {}'.format(
            self.ingest['copyright_date']
        ))

        coverFetch = HathiCover(self.ingest['htid'])
        pageURL = coverFetch.getPageFromMETS()
        if pageURL is not None:
            logger.debug('Add cover image {} to instance'.format(pageURL))
            self.instance.addClassItem('links', Link, **{
                'url': pageURL,
                'media_type': 'image/jpeg',
                'flags': {
                    'cover': True,
                    'temporary': True,
                }
            })

        self.parsePubInfo(self.ingest['publisher_pub_date'])

        # Add instance to parent work
        self.work.instances.append(self.instance)

    def buildItem(self):
        """HathiTrust items also correspond to a single item, the digitzed
        version of the book being described. From this record we can derive two
        links, a link to the HathiTrust reader page and a page for a direct
        download of the PDF copy of the book.
        """
        self.item.source = 'hathitrust'
        self.item.content_type = 'ebook'
        self.item.modified = self.modified

        logger.info('Creating item record for instance {}'.format(
            self.instance
        ))

        logger.debug('Setting htid {} for item'.format(self.ingest['htid']))
        self.parseIdentifiers(self.item, 'hathi', 'htid')

        logger.debug(
            'Storing direct and download links based on htid {}'.format(
                self.ingest['htid']
            ))
        # The link to the external HathiTrust page
        self.item.addClassItem('links', Link, **{
            'url': 'https://babel.hathitrust.org/cgi/pt?id={}'.format(
                self.ingest['htid']
            ),
            'media_type': 'text/html',
            'flags': {
                'local': False,
                'download': False,
                'images': True,
                'ebook': True
            }
        })

        # The link to the direct PDF download
        self.item.addClassItem('links', Link, **{
            'url': 'https://babel.hathitrust.org/cgi/imgsrv/download/pdf?id={}'.format(self.ingest['htid']),
            'media_type': 'application/pdf',
            'flags': {
                'local': False,
                'download': True,
                'images': True,
                'ebook': True
            }
        })

        logger.debug('Storing repository {} as agent'.format(
            self.ingest['provider_entity']
        ))
        self.item.addClassItem('agents', Agent, **{
            'name': HathiRecord.sourceCodes[self.ingest['provider_entity'].lower()],
            'roles': ['repository']
        })

        logger.debug('Storing organization {} as agent'.format(
            self.ingest['responsible_entity']
        ))
        self.item.addClassItem('agents', Agent, **{
            'name': HathiRecord.sourceCodes[self.ingest['responsible_entity'].lower()],
            'roles': ['responsible_organization']
        })

        logger.debug('Storing digitizer {} as agent'.format(
            self.ingest['digitization_entity']
        ))
        self.item.addClassItem('agents', Agent, **{
            'name': HathiRecord.sourceCodes[self.ingest['digitization_entity'].lower()],
            'roles': ['digitizer']
        })

        # Add item to parent instance
        self.instance.formats.append(self.item)

    def createRights(self):
        """HathiTrust contains a strong set of rights data per item, including
        license, statement and justification fields. As this metadata is
        applicable to all levels in the SFR model, constructing a stand-alone
        rights object is the best way to ensure that accurate rights data
        is assigned to the records extracted from HathiTrust.
        """

        logger.info('Creating new rights object for row {}'.format(
            self.ingest['htid']
        ))

        self.rights.source = 'hathi_trust'
        self.rights.license = HathiRecord.rightsValues[self.ingest['rights']]['license']
        self.rights.rights_statement = HathiRecord.rightsValues[self.ingest['rights']]['statement']
        self.rights.rights_reason = HathiRecord.rightsReasons[self.ingest['rights_statement']]

        self.rights.addClassItem('dates', Date, **{
            'display_date': self.ingest['rights_determination_date'],
            'date_range': self.ingest['rights_determination_date'],
            'date_type': 'determination_date'
        })

        self.rights.addClassItem('dates', Date, **{
            'display_date': self.ingest['copyright_date'],
            'date_range': self.ingest['copyright_date'],
            'date_type': 'copyright_date'
        })

        # At present these rights are assigned to all three levels in the SFR
        # model work, instance and item. While this data certainly pertains to
        # the instance and item records retrieved here, its relevance is
        # unclear for the work record. It will be possible to have conflicting
        # rights statements for works and instances
        self.work.rights = [self.rights]
        self.instance.rights = [self.rights]
        self.item.rights = [self.rights]

    def parseIdentifiers(self, record, idType, key):
        """Iterate identifiers, splitting multiple values and storing in
        the indicated record.
        """
        if key not in self.ingest:
            logger.warning('{} not a valid type of identifier'.format(key))
            return
        idInstances = self.ingest[key].split(',')
        if len(idInstances) >= 1 and idInstances[0] != '':
            for typeInst in idInstances:
                logger.debug('Storing identifier {} ({}) for {}'.format(
                    typeInst,
                    idType,
                    record
                ))
                record.addClassItem('identifiers', Identifier, **{
                    'type': idType,
                    'identifier': typeInst.strip(),
                    'weight': 1
                })

    def parseAuthor(self, authorStr):
        """Hathi data files include an author column that combines author name
        with their birth and death dates (sometimes). This method parses
        those dates from the name and assigns them as Date objects to the
        constructed agent record. This record is then assigned to the work.
        """
        logger.info('Storing author {} for work {}'.format(
            authorStr,
            self.work
        ))
        authorDateGroup = re.search(r'([0-9\-c?\'.]{4,})', authorStr)
        authorDates = None
        if authorDateGroup is not None:
            authorDates = authorDateGroup.group(1)
            authorName = authorStr.replace(authorDates, '').strip(' ,.')
            logger.debug('Found lifespan dates {}'.format(authorDates))
        else:
            authorName = authorStr
            logger.debug('Found no lifespan dates')

        authorRec = Agent(
            name=authorName,
            role='author'
        )

        if authorDates is not None:
            logger.info('Creating date objects for author lifespan')
            lifespan = authorDates.strip(' ,.').split('-')
            if len(lifespan) == 1:
                logger.debug('Found single date, default to death_date')
                dateType = 'death_date'
                datePrefix = re.search(r' b(?: |\.)', authorStr)
                if datePrefix is not None:
                    authorRec.name = re.sub(
                        r' b(?: |\.|$)', '',
                        authorName
                    ).strip(' ,.')
                    logger.debug('Detected single birth_date (living author)')
                    dateType = 'birth_date'

                logger.debug('Storing single date {} of type {}'.format(
                    lifespan[0],
                    dateType
                ))
                authorRec.addClassItem('dates', Date, **{
                    'display_date': lifespan[0],
                    'date_range': lifespan[0],
                    'date_type': dateType
                })

            else:
                logger.debug('Storing lifespan {}-{} as dates'.format(
                    lifespan[0],
                    lifespan[1]
                ))
                authorRec.addClassItem('dates', Date, **{
                    'display_date': lifespan[0],
                    'date_range': lifespan[0],
                    'date_type': 'birth_date'
                })
                authorRec.addClassItem('dates', Date, **{
                    'display_date': lifespan[1],
                    'date_range': lifespan[1],
                    'date_type': 'death_date'
                })
        logger.debug('Appending agent record {} to work'.format(authorRec))
        self.work.agents.append(authorRec)

    def parsePubPlace(self, pubPlace, countryCodes):
        """Attempt to load a country/state name from the countryCodes list
        If not found simply include the code as the publication place
        NOTE: If this occurs frequently check the MARC site for an updated
        list and issue a pull request to replace the XML included here.
        """
        try:
            self.instance.pub_place = countryCodes[pubPlace.strip()]
            logger.debug('Setting decoded pub_place to {}'.format(
                self.instance.pub_place
            ))
        except KeyError:
            self.instance.pub_place = pubPlace.strip()
            logger.warning('Failed to decode pub_place code, setting to raw code {}'.format(self.instance.pub_place))

    def parsePubInfo(self, imprintInfo):
        """Similar to authors 'imprint' or publication info is combined into
        a single column. This extracts the date and attempts to clean up
        any trailing punctuation left over from this operation.
        """
        logger.info('Storing publication {} info for instance {}'.format(
            imprintInfo,
            self.instance
        ))
        pubDateGroup = re.search(r'([0-9\-c?\'.]{4,})', imprintInfo)
        if pubDateGroup is not None:
            pubDate = pubDateGroup.group(1).strip(' ,.')
            logger.debug('Storing publication date {}'.format(pubDate))
            self.instance.addClassItem('dates', Date, **{
                'display_date': pubDate,
                'date_range': pubDate,
                'date_type': 'publication_date'
            })
            imprintInfo = imprintInfo.replace(pubDate, '')

        imprintInfo = re.sub(r'[\W]{2,}$', '', imprintInfo)
        logger.debug('Storing publisher as agent {}'.format(imprintInfo))
        self.instance.addClassItem('agents', Agent, **{
            'name': imprintInfo,
            'roles': ['publisher']
        })

    def parseGovDoc(self, govDocStatus, sourceID):
        if str(govDocStatus).lower() in ['1', 't']:
            govDocStatus = True
        else:
            govDocStatus = False
        self.work.addClassItem('measurements', Measurement, **{
            'quantity': 'government_document',
            'value': int(govDocStatus),
            'weight': 1,
            'taken_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_id': sourceID
        })
        logger.debug('Storing gov_doc status to {}'.format(str(govDocStatus)))
