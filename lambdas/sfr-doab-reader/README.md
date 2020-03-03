# SFR Directory of Open Access Books Data Parser

[![Build Status](https://travis-ci.com/NYPL/sfr-doab-reader.svg?branch=development)](https://travis-ci.com/NYPL/sfr-doab-reader) [![GitHub version](https://badge.fury.io/gh/nypl%2Fsfr-doab-reader.svg)](https://badge.fury.io/gh/nypl%2Fsfr-doab-reader)

A function for parsing Directory of Open Access Books (DOAB) data into a SFR-compliant data model. The records from DOAB are comprised of books that have been explicitly issued with a CreativeCommons by-nc-nd 4.0 license and which are readable both online and as a downloadable PDF. 

This function retrieves these records by querying DOAB's OAI-PMH feed for records updated in a provided time period, parsing them, and placing them in the SFR data ingest pipeline (alongside records also retrieved from Project Gutenberg and HathiTrust)

## Requirements
Python 3.6+ (written with Python 3.7)

## Dependencies

- boto3
- lxml
- marcalyx
- pyyaml

## Note

This function is based on the [Python Lambda Boilerplate](https://github.com/NYPL/python-lambda-boilerplate) and can be run/development with the help of the `make` commands made available through that repository.

## Environment Variables

- LOG_LEVEL: Set to a standard logging level (default: info)
- DOAB_OAI_ROOT: Root URL of the DOAB OAI-PMH feed (currently: https://www.doabooks.org/oai?verb=ListRecords)
- LOAD_DAYS_AGO: Number of days ago from which to load DOAB records (*Note*: Must be provided as a string, e.g. `'1'`)
- MARC_RELATORS: URL to LoC hosted JSON document of MARC relators (currently: http://id.loc.gov/vocabulary/relators.json)
- OUTPUT_STREAM: Name of Kinesis stream to place parsed records into
- OUTPUT_SHARD: Shard to place records in (A good default value is: `'0'`)

## Event Triggers

This function can be trigged through a CloudWatch event to run at a regularly scheduled interval, or can be trigger to run locally to retrieve a single record. This mode of operation is useful for testing. The event required to trigger this single ingest should be formatted as follows:

``` JSON
{
    "source": "local.url",
    "url": "[URL to single OAI-PMH record]"
}
```

## Testing/Development

It is recommended that local development and testing of this function be done in a virtual environment.

Tests can be run via the `make test` and linting through `make lint` command and local execution (using a local CSV file) can be done with `make local-run`

To deploy the function to a Lambda in you AWS environment run `make deploy ENV=[environment]` where environment designates the desired YAML file you'd like to deploy with.
