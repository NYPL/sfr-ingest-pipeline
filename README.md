# SFR Database Manager
This is a Lambda function that manages writing updates to our postgres database instance. It will make updates where necessary (if a record already exists) or insert a new record. This relies on SQLAlchemy to manage the data model and Alembic to manage data migrations within the database. This allows for the tracking of data model changes over time and the ability to create new database instances.

## Version
v0.0.1

## Deployment
This app is deployed via travisCI, with a pull request successfully building triggering a deployment to the relevant environment.

## Environment Variables
A relatively large number of environment variables should be set to manage the various connections this function must make to read, store and output data to various sources:

- LOG_LEVEL: Set the relevant log level (will appear in the cloudwatch logs)
- DB_HOST: Host of our Postgresql instance
- DB_PORT: Postgresql port on host above
- DB_NAME: Name of Postgresql database
- DB_USER: User for specified database
- DB_PASS: Password for above user
- OUTPUT_SQS: URL for SQS queue where updated records are placed (see below for format)
- EPUB_STREAM: Kinesis stream for parsing and local storage of ePub URLs
- CLASSIFY_STREAM: Kinesis stream of work identifiers to be processed by the OCLC Classify service

## Data Model and Message Formats
With multiple interfaces, this function communicates in several different ways. It also contains the overall data model for the Postgresql database. Each of these is detailed at the links below

[Data Model](docs/datamodel.md)

Input Message Formats
- Work
- Instance (TODO)
- Item (TODO)

Output Message Format

ePub Ingest Message Format
