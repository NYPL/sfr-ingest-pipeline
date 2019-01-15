# ElasticSearch Data Model

## Overview
This is a high-level description of the structure of the ElasticSearch index that is used to serve records to the API and, through that, end-users, either directly or through the front-end React application.

This model bears a strong resemblance to the intermediate data model that is used in the ingest pipeline, in that it represents each Work as a document that contains sub-documents for instances, agents, etc. However, the ElasticSearch model somewhat flattens the data structure for easier retrieval/parsing. The best example of this is the date class, which is omitted here in favor of explicit fields for the dates that will be actively used. Further, certain fields, especially raw text/blob/JSON fields, are omitted, as they likely are not necessary to serve to users.

## Meta `_id` Field
By default ElasticSearch assigns a random, unique `id` number in the standard `meta` object attached to each document. This identifier is generally the quickest/easiest way to retrieve a single document from the index. As each Work record is uniquely identified by a UUID generated on insert, the ElasticSearch `id` value is overridden with the UUID. This allows for simple retrieval/updating of records in ElasticSearch.

## Model Inheritance
Not included in the model documentation below are the `date_created` and `date_modified` fields, which are universal in the database and applied through class inheritance for ElasticSearch.

## Model

### Work
- title (Text)
  - keyword (Keyword)
- sort_title (Keyword)
- uuid (Keyword)
- language (Keyword)
- license (Keyword)
- rights_statement (Text)
  - keyword (Keyword)
- medium (Text)
  - keyword (Keyword)
- series (Text)
  - keyword (Keyword)
- series_position (Short)
- issued (DateRange)
- created (DateRange)
- alt_titles (Text)
  - keyword (Keyword)
- subjects (Nested)
- agents (Nested)
- measurements (Nested)
- links (Nested)
- instances (Nested)

### Instance
- title (Text)
  - keyword (Keyword)
- sub_title (Text)
  - keyword (Keyword)
- alt_titles (Text)
  - keyword (Keyword)
- pub_place (Text)
  - keyword (Keyword)
- pub_date (DateRange)
- copyright_date (DateRange)
- edition (Text)
  - keyword (Keyword)
- edition_statement (Text)
  - keyword (Keyword)
- language (Keyword)
- extent (Text)
- license (Text)
  - keywords (Keyword)
- rights_statement (Text)
  - keywords (Keyword)
- items (Nested)
- agents (Nested)
- measurements (Nested)
- identifiers (Nested)
- links (Nested)

### Item
- source (Keyword)
- content_type (Keyword)
- modified (DateRaneg)
- drm (Keyword)
- rights_uri (Keyword)
- agents (Nested)
- measurements (Nested)
- identifiers (Nested)
- links (Nested)
- access_reports (Nested)

### Identifier
- id_type (Keyword)
- identifier (Keyword)

### Agent
- name (Text)
  - keyword (Keyword)
- sort_name (Keyword)
- aliases (Text)
  - keyword (Keyword)
- lcnaf (Keyword)
- viaf (Keyword)
- birth_date (DateRange)
- death_date (DateRange)
- biography (Text)
- links (Nested)

### Link
- url (Keyword)
- media_type (Keyword)
- rel_type (Keyword)
- thumbnail (Keyword)

### Subject
- authority (Keyword)
- uri (Keyword)
- subject (Text)
  - keyword (Keyword)
- weight (HalfFloat)

### AccessReport
- ace_version (Keyword)
- score (HalfFloat)
- measurements (Nested)

### Measurement
- quantity (Keyword)
- value (Float)
- weight (HalfFloat)
- taken_at (Date)
