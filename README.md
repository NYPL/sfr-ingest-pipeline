# Gutenberg Ingest Lambda for ResearchNow

[![Build Status](https://travis-ci.com/NYPL/sfr-gutenberg-reader.svg?token=Fv4twsPZbkerqgdJB89v&branch=development)](https://travis-ci.com/NYPL/sfr-gutenberg-reader) [![GitHub version](https://badge.fury.io/gh/nypl%2Fsfr-gutenberg-reader.svg)](https://badge.fury.io/gh/nypl%2Fsfr-gutenberg-reader)

This lambda reads recently published/updated files from Project Gutenberg and processes them for the ResearchNow project.

## Process

This ingest process utilizes the GITenberg project (https://github.com/gitenberg) which maintains the Project Gutenberg collection as a set of repositories. It queries this collection via the GitHub GraphQL API and uses the returned RDF file to build a basic metadata profile of each volume. It is designed to be run nightly and get records updated in the past 24 hours, but this can be adjusted to run as frequently (or infrequently) as necessary.

## Output

The lambda writes a basic metadata block to a Kinesis stream. That block includes:

- Title/Alt Title
- Publisher
- Created
- Updated
- Subjects
- ePub Formats
- Entities (creator, editor, etc.)

## Requirements

- nodejs10.x

## Dependencies

- apollo
- axios
- csvtojson
- graphql
- js-yaml
- mime-types
- rdflib
- xml2js

## Development

### Local Development

After installing dependencies this function can be run locally with `npm run local-run` which will execute the function with the parameters defined in `config/local.env`

### Deployment

This function will be automatically deployed to AWS Lambda when merged into `development` to deploy a specific branch/to a different environment this can be done with `npm run deploy-[ENVIRONMENT]`

### Testing

The test suite can be run with the standard `npm test`