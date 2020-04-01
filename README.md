# ResearchNow Data Ingest Pipeline

## Summary/Purpose

This repository represents the ETL pipeline that produces the data discoverable on [researchnow-beta.nypl.org](researchnow-beta.nypl.org). This pipeline extracts metadata records representing distinct instances of bibliographic records and transforms them into a simplified FRBR model to improve their discoverability and expose connection between separate book digitization projects.

This is a serverless infrastructure built on AWS and is primarily composed of Lambda functions with various supporting infrastructure. The records produced here are made available through a public API ([documented here](https://dev-platformdocs.nypl.org/#/research-now)).

## Requirements

- Python 3.6/3.7/3.8
- Node.js 12.16.1
- postgreSQL 9.4+
- ElasticSearch 6.7
- Redis

## Dependencies

All dependencies below should be installed in a virtualenv

### Node.js

- @daisy/ace -- 1.0.2
- apollo-boost -- 0.1.20
- apollo-cache-inmemory -- 1.3.9
- apollo-client -- 2.4.5
- apollo-link-context -- 1.0.9
- apollo-link-error -- 1.1.1
- apollo-link-http -- 1.5.5
- apollo-link-timeout -- 1.1.8
- aws-sdk -- 2.437.0
- axios -- 0.19.0
- body-parser -- 1.19.0
- bodybuilder -- 2.2.20
- config -- 2.0.1
- cvstojson -- 2.0.8
- dotenv -- 7.0.1
- elasticsearch -- 15.1.1
- express -- 4.16.4
- fs-extra -- 7.0.1
- graphql -- 14.0.2
- graphql-tag -- 2.10.0
- js-yaml -- 3.13.1
- knex -- 0.19.5
- lambda-env-vars -- 0.4.0
- mime-types -- 2.1.24
- mock-knex -- 0.4.7
- moment -- 2.24.0
- node-fetch -- 2.2.1
- pg -- 7.17.0
- rdflib -- 0.19.1
- request -- 2.88.0
- sqs-consumer -- 5.2.0
- swagger-client -- 3.9.6
- swagger-parser -- 6.0.2
- swagger-ui-express -- 4.1.2
- unzip-stream -- 0.3.0
- xml2js -- 0.4.19

### Python

- alembic
- babelfish
- beautifulsoup4
- boto3
- elasticsearch -- 6.3.1
- elasticsearch-dsl -- 6.3.1
- lxml
- marcalyx
- psycopg2-binary
- pycountry
- python-lambda
- python-levenshtein
- pyyaml
- redis
- requests
- requests_oauthlib
- sqlalchemy

### Dependency Note

The core ORM model is a dependency of several components of this pipeline, but due to AWS Lambda configuration (see the `core/sfr-db-core` documentation for more on this) this functionality cannot be included as a normal dependency. To work with this project please install the package at `core/sfr-db-core` in your virtualenv for this project.

## Installation

### TODO

- Create local run option for entire pipeline (via LocalStack or other solution)
- Normalize all `make` and `npm` commands across components
- Create single script for running configuration/installation for all components
- Add additional documentation for each component

## Usage

This pipeline cannot currently be run as a single application locally. To install individual components, navigate to the desired component, ensure that the dependencies are installed and follow the component's documentation for setting up any `config` or `environment` variables that need to be changed or updated. From there the component can be run with `make run-local` or `npm run local-run` depending on the component.

### Exceptions

The search API can be started with `npm run start-dev` and the postrgeSQL ORM cannot be run but can be compiled as a docker image with the commands in the documentation there.

## Testing

Each component can be tested individually (project wide unit and integration tests are in development) by navigating to the appropriate component and running `make test` or `npm test` both will produce coverage reports.

## Development

Any changes to any component of this pipeline should be made in a feature branch, have a PR opened and be merged into the `development` branch, which is the main working branch for this project.

## Components

The pipeline is made of the following components

- Core Packages
  - `sfr-db-core` Sets up and controls the ORM for the postgreSQL database. This data model largely defines how other components can interact with this data.
- Applications
  - `sfr-ace-reporter` A Node.js Express application that parses ePub files with the `daisy/ace` accessibility tool and generates a report on their general level of accessibility.
  - `sfr-search-api` A Node.js Express application that provides the public search API for the ResearchNow project. All data ingested and produced in this pipeline is exposed through this application.
- Lambdas
  - `sfr-clstr-manager` Applies the kMeans Machine Learning algorithm to the instances associated with a single work and produces the derived edition records. The resulting objects are what is provided to users for discovery and display.
  - `sfr-cover-search` Queries the book cover providers being used for this project and returns a URI to the first match found for the provided standard identifier.
  - `sfr-cover-writer` Takes the retrieved cover image URIs, fetches the associated file and stores a processed version in an AWS s3 bucket. These files are what is displayed on ResearchNow.
  - `sfr-db-manager` This takes newly retrieved metadata records and checks for existing records in the database. If found, the records are passed to the updater, if not they are persisted to the database, and if possible passed to the enhancement stage for enrichment.
  - `sfr-db-updater` This takes metadata records that represent objects to be updated in the database and applies these updates.
  - `sfr-doab-reader` Fetches new metadata records from the [Directory of Open Access Books Project](https://doabooks.org) and passes them for ingest to the database manager. This generally runs nightly to fetch recent updates but can also run arbitrary batches if needed to populate a new database
  - `sfr-epub-writer` Takes ePub files found as part of the data fetching process and stores them in a s3 bucket for display/use through the ResearchNow application
  - `sfr-es-manager` Gathers recent updates in the database and passes these records to the clustering function which will process them and index them in the ElasticSearch index.
  - `sfr-gutenberg-reader` Fetches metadata records from [Project Gutenberg](https://gutenberg.org) and passes them for ingest to the database. This also runs on a nightly schedule, or over custom defined segments of the Gutenberg collection
  - `sfr-hathi-reader` Fetches metadata records from [HathiTrust](https://hathitrust.org) and passes them for ingest to the database. Similarly runs on a nightly schedule, with additional batch ingest capabilities
  - `sfr-oclc-classify` Starts the metadata enhancement process, taking simple work records and attempting to find matching work records in OCLC. Matching metadata records are fetched and merged to produce a more accurate representation of this work.
  - `sfr-oclc-lookup` Fetches individual catalog records for matches found through the classification step. These MARC records are parsed, with the relevant metadata eventually being persisted in the database.
  - `sfr-unglueit-lookup` Searches for and returns any matching work summaries for standard numbers.
  - `sfr-viaf-lookup` Queries the VIAF service for personal and corporate names and returns the VIAF number for found matches, used to normalize names and name searches in the ResearchNow application.
  - `sfr-publisher-reader` A reader for parsing records from various smaller open access/public domain projects. Includes a plugin structure to allow for easier addition of new sources to the project.
