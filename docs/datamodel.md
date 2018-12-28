# Data Model
The data model for the SFR project is closely modeled on the FRBR framework and borrows concepts from the model defined for the [NYPL Library Simplified Project](https://github.com/NYPL-Simplified/server_core/tree/master/model).

## Tables
- [Works](#works)
  - [Alternate Titles](#altTitles)
  - [Import JSON](#json)
- [Instances](#instances)
- [Items](#items)
  - [Accessibility Reports](#reports)
- [Agents](#agents)
  - [Aliases](#aliases)
- [Subjects](#subjects)
- [Measurements](#measurements)
- [Identifiers](#identifiers)
- [Links](#links)

## Works <a name="works"></a>
The Work table is the highest level representation of a document in the SFR collection. It covers the intellectual content of a work, including the title, language, and other data that pertains to the the document as an abstract intellectual entity.

### Fields
- uuid (UUID)
- title (Unicode)
- sort_title (Unicode)
- sub_title (Unicode)
- language (Char(2))
- issued (Date)
- published (Date)
- license (Unicode)
- rights_statement (Unicode)
- medium (Unicode)
- series (Unicode)
- series_position (Integer)

### Relationships
- Agents
- Subjects
- Alt Titles
- Import JSON
- Instances
- Identifiers
- Measurements
- Links

## Alternate Titles <a name="altTitles"></a>
Each work can have multiple titles, and some works can have many such titles. Those are stored in a related table for flexibility purposes

### Fields
- title (Unicode)
- work_id (Integer)

### Relationships
- Works

## Import JSON <a name="json"></a>
It is possible to have multiple imports that include data for a single work record. In order to preserve our knowledge about what data comes from which source, and to enable the rebuilding of the database should an error occur.

### Fields
- data (JSON)
- work_id (Integer)

### Relationships
- Works

## Instances <a name="instances"></a>
The instance table covers, essentially, the edition-level metadata pertaining to a work. Each instance is a distinct expression of the work, but not a specific copy of that work. It can have its own title and publication date that pertain specifically to this version.

### Fields
- title (Unicode)
- sub_title (Unicode)
- pub_place (Unicode)
- pub_date (Date)
- edition (Unicode)
- edition_statement (Unicode)
- table_of_contents (Unicode)
- copyright_date (Date)
- language (Char(2))
- work_id (Integer)

### Relationships
- Works
- Items
- Agents
- Links
- Measurements
- Identifiers

## Items <a name="items"></a>
Items represent specific copies of an instance/edition. In the case of SFR this indicates a specific digital copy of an ebook. These will generally be stored locally, however it will be possible for them to be accessed at a remote URL

### Fields
- source (Unicode)
- content_type (Unicode)
- modified (Datetime)
- drm (Unicode)
- rights_uri (Unicode)

### Relationships
- Instances
- Agents
- Identifiers
- Measurements
- Links
- Accessibility Reports

## Accessibility Reports <a name="reports"></a>
Each item (epub) is scored on its accessibility through the Ace Reporting tool. This data is stored and used to inform users about the overall accessibility of the epub file

### Fields
- score (Float)
- ace_version (Unicode)
- report_json (JSON)
- item_id (Integer)

### Relationships
- Measurements

## Agents <a name="agents"></a>
These are individuals, organizations or families that are involved in the creation, production or maintenance of a work or one of its derivative forms. These range from the original author, to an individual involved with the preservation process. Each agent is associated with a relevant record through a "role", which is stored in a secondary joining table and which allows for multiple distinct relationships between a single record and a single agent.

### Fields
- name (Unicode)
- sort_name (Unicode)
- lcnaf (Unicode)
- viaf (Unicode)
- biography (Unicode)
- birth_date (Date)
- death_date (Date)

### Relationships
- Works
- Instances
- Items
- Links

## Aliases <a name="aliases"></a>
An agent may have name variations provided by different sources (but be uniquely identified by a VIAF or LCNAF identifier), and those variations should be stored for discovery purposes

### Fields
- alias (Unicode)
- agent_id (Integer)

### Relationships
- Agents

## Subjects <a name="subjects"></a>
These are standard subjects, which are related to works. They cover the intellectual content of the work and are drawn from the standard authorities such as Getty and the Library of Congress

### Fields
- authority (Unicode)
- uri (Unicode)
- subject (Unicode)
- weight (Float)

### Relationships
- Works

## Measurements <a name="measurements"></a>
Measurements provides an abstract class for capturing quantitative data about the information being stored for a specific record. For example, instances are generally associated with a specific number of digital and physical library holdings. This type of data is recorded in this table.

### Fields
- quantity (Unicode)
- value (Float)
- weight (Float)
- taken_at (Datetime)

### Relationships
- Works
- Instances
- Identifiers
- Accessibility Reports

## Identifiers <a name="identifiers"></a>
These are unique identifiers drawn from a range of sources that can uniquely identify one of the core (Work, Instance, Item) records. They are either provided by a data source or retrieved through the data enrichment process.

This is not structured as a single table, but as a management table with a number of tables, one for each type of identifier we are storing.

### Fields
- type (Unicode)
- value (Unicode)

### Relationships
- Works
- Instances
- Items

## Links <a name="links"></a>
These are references to external or internal resources that can be accessed via an URI. The table encodes several fields pertaining to each reference.

### Fields
- url (Unicode)
- media_type (Unicode)
- content (Unicode)
- rel_type (Unicode)
- rights_uri (Unicode)
- thumbnail (Link)

### Relationships
- Works
- Instances
- Items
- Agents
