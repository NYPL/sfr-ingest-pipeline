# SFR Database Manager

[![Build Status](https://travis-ci.com/NYPL/sfr-db-manager.svg?branch=development)](https://travis-ci.com/NYPL/sfr-db-manager)
[![GitHub version](https://badge.fury.io/gh/nypl%2Fsfr-db-manager.svg)](https://badge.fury.io/gh/nypl%2Fsfr-db-manager)

This is a Lambda function that manages writing new records to the ResearchNow/SFR postgres database instance. Any records where an existing match is found are deferred to the sfr-db-updater function, which implements additional logic for finding matches and merging records. This function is designed to quickly ingest new insert requests and start the data enrichment and ePub storage components of the data pipeline.

This repository also contains the "source of truth" for the database model and migrations are defined in the `alembic` directory of this repository.

## Version

v0.1.0

## Deployment
This function (and other similar functions) rely on the `psycopg2-binary` library which requires a set of staticly linked libraries to be deployed on Linux. The Amazon AMI for Lambda functions does not automatically include these libraries and as a result cannot be deployed from non-Amazon linux environments. To properly deploy this and other functions, do so from either an EC2 instance created with the Amazon Linux image, or from a Docker container created in a similar fashion.

## Environment Variables

- LOG_LEVEL: Set the relevant log level (will appear in the cloudwatch logs)
- DB_HOST: Host of our Postgresql instance
- DB_PORT: Postgresql port on host above
- DB_NAME: Name of Postgresql database
- DB_USER: User for specified database
- DB_PASS: Password for above user
- EPUB_STREAM: Kinesis stream for parsing and local storage of ePub URLs
- CLASSIFY_STREAM: Kinesis stream of work identifiers to be processed by the OCLC Classify service

## Dependencies
- pycountry
- pyscopg2-binary
- pyyaml
- redis
- SQLAlchemy

## Control Flow
This function manages the overall control flow of the SFR/ResearchNow ingest pipeline and connects to several other Lambda functions, in addition to the central postgres instance. These are:
1) The `sfr-db-updater` function via a Kinesis stream. This function is passed any records that update an existing row of the database.
2) The `sfr-oclc-frbizer` function via a Kinesis stream. This handles the initial phase of the data enhancement process.
3) The `sfr-epub-manager` function via a Kinesis stream. This handles storing any ePub files locally in S3, preparing them to be served by the front-end application.


### Data Model
[Data Model](docs/datamodel.md)

## Input/Output Formats
[Input Message Format](docs/inputformats.md)

[Output Message Format](docs/outputformat.md)

[ePub Ingest Message Format](docs/epubmessageformat.md)
