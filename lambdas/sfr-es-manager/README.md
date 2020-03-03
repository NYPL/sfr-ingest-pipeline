# SFR ElasticSearch Manager

[![Build Status](https://travis-ci.com/NYPL/sfr-elasticsearch-manager.svg?branch=development)](https://travis-ci.com/NYPL/sfr-elasticsearch-manager) [![GitHub version](https://badge.fury.io/gh/nypl%2Fsfr-elasticsearch-manager.svg)](https://badge.fury.io/gh/nypl%2Fsfr-elasticsearch-manager) 

This Lambda function manages the SFR ElasticSearch index, reflecting updates from the postgreSQL persistence layer into an ElasticSearch index (used for record retrieval by APIs/the SFR front-end application)

## Dependencies

- coverage
- flake8
- psycopg2-binary
- python-lambda
- pyyaml
- SQLAlchemy

## Environment Variables
- LOG_LEVEL: Set the relevant log level (will appear in the cloudwatch logs)
- DB_HOST: Host of our Postgresql instance
- DB_PORT: Postgresql port on host above
- DB_NAME: Name of Postgresql database
- DB_USER: User for specified database
- DB_PASS: Password for above user

## Input
The function reads from an SQS stream that contains messages pushed when a database update is executed. These messages contain a the type of record being updated and an unique identifier for that record. Example:
```
{
  'type': 'work',
  'identifier': 'XXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'
}
```

## Deployment
Deployment can be executed through one of several methods:
1) Deploy directly from your development environment using `make deploy ENV=[environment]` where `environment` corresponds to one of the YAML files in your `config` directory
2) Deploy through the AWS console by building locally with `make build` and copying the generated file from you `dist` directory and to the Kinesis UI.
3) **TO DO** Run an automated deploy on successful pull request through travisCI

## Testing
The test suite is run with `make test`. To view the current coverage report run `make coverage-report`.

Sample events can be executed by creating a `event.json` file in your project's root directory with a mock SQS event. With this file running `make run-local` will execute the function and return/log any output. **Warning** this will utilize variables defined in the `development.yaml` file of your project, potentially updating your development environment.

## Linting
To run the flake8 linter with standard guidelines use `make lint`
