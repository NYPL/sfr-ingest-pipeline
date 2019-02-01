
# SFR HathiTrust Data Parser

A function for parsing HathiTrust item records into a SFR-compliant data model. This reads data from spreadsheets made available through the [Hathifiles Page](https://www.hathitrust.org/hathifiles). Each file contains the previous days updates, which are put into the SFR data ingest Kinesis stream, for processing into the database and search index.

## Version

v0.0.1

## Requirements

Python 3.6+ (written with Python 3.7)

## Dependencies

- coverage
- flake8
- python-lambda
- python-levenshtein
- pyyaml

## Note

This function is based on the [Python Lambda Boilerplate](https://github.com/NYPL/python-lambda-boilerplate) and can be run/development with the help of the `make` commands made available through that repository.

## Environment Variables

- LOG_LEVEL

## Event Triggers

This function can be trigged through a CloudWatch event to run at a regularly scheduled interval (likely every 24 hours given the frequency of published updates from HathiTrust), or can be trigger to run locally with a provided CSV file. This mode of operation is useful for testing or ensuring that specific HathiTrust records are up to date in the SFR collection. The event required to trigger this manual operation should be a JSON document formatted as follows:

``` JSON
{
    "source": "local.file",
    "localFile": "/path/to/csv_file"
}
```

## Testing/Development

It is recommended that local development and testing of this function be done in a virtual environment.

Tests can be run via the `make test` and linting through `make lint` command and local execution (using a local CSV file) can be done with `make local-run`

To deploy the function to a Lambda in you AWS environment run `make deploy ENV=[environment]` where environment designates the desired YAML file you'd like to deploy with.
