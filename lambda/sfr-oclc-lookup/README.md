# OCLC Lookup Service

[![Build Status](https://travis-ci.com/NYPL/sfr-oclc-catalog-lookup.svg?branch=development)](https://travis-ci.com/NYPL/sfr-oclc-catalog-lookup)
![GitHub tag (latest SemVer)](https://img.shields.io/github/tag/nypl/sfr-oclc-catalog-lookup.svg)

A lambda function that takes OCLC identifiers and returns a parsed version of the MARCXML record that is returned through the [OCLC Catalog lookup](https://www.oclc.org/developer/develop/web-services/worldcat-search-api/bibliographic-resource.en.html) service.

The returned data corresponds to the Instance level records in the SFR data model.

## Note
This code is based on the [Python Lambda Boilerplate](https://github.com/NYPL/python-lambda-boilerplate), and as a result can be run through the `make` commands detailed there such as `make test` and `make local-run`

## Dependencies

- boto3
- marcalyx
- python-lambda
- pyyaml
- requests

## Dev Dependencies

- coverage
- flake8


## Environment Variables
- LOG_LEVEL
- OUTPUT_REGION
- OUTPUT_KINESIS
- OUTPUT_SHARD
- OCLC_KEY **important** Necessary to make requests to OCLC catalog

## Input
Accepts a simple record containing a `type` of identifier, currently restrict to OCLC identifiers and the `identifier` value itself. Example:
```
{
  'type': 'oclc',
  'identifier': '000000000000'
}
```

## Output
An **Instance** record from the SFR Data Model

## Deployment
Deployment is managed through the makefile included in this repository, with different environments defined in the `config/` directory. To deploy to a defined environment run `make deploy ENV=[environment]`

An alternative deployment method is to build the Lambda function locally and manually upload the file to AWS. To do so, run `make build` and take the created zip in the `dist/` directory and upload the file through the AWS console

## Testing
Tests can be ran with `make test`

To run a sample event (which must be defined in your local `event.json` file), run `make run-local`. **Warning** This will use the settings you have defined in your `development.yaml` file, including outputting any generated records to Kinesis streams defined there

Linting is available through `make lint` using the standard flake8 guidelines
