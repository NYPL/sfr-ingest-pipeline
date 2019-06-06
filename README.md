
# SFR HathiTrust Data Parser

A function for parsing HathiTrust item records into a SFR-compliant data model. This reads data from spreadsheets made available through the [Hathifiles Page](https://www.hathitrust.org/hathifiles). Each file contains the previous days updates, which are put into the SFR data ingest Kinesis stream, for processing into the database and search index.

## Version

v0.0.2

## Requirements

Python 3.6+ (written with Python 3.7)

## Dependencies

- coverage
- flake8
- python-lambda
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


## A Note on Data
Several transformations are applied to the HathiTrust data as it is received in order to best conform it to match the SFR data model.
1. The `htid` that uniquely identifies each item can be, and is, used to create URLs at which the item itself (a PDF file) can be viewed and downloaded
2. HathiTrust data contains a robust set of rights data, this is combined into a single class in the SFR data model and associated with both the `instance` and `item` that are created from the Hathi item.
3. In the TSV format accessed here, several metadata fields are collapsed into single columns. This data exists separately in MARC files accessible via the HathiTrust API. If this data needs to be accessed separately, an additional step calling this API will need to be added to this function.
4. Occasionally data will be misordered in individual rows of the TSV. The function attempts to detect these and skip them as we cannot reliably reorganize the data. Such events are logged.
5. The data in the `description` column of the TSV file is treated as volume identifiers. This is useful for distinguishing between different volumes of a periodical and is used in the database manager function for this purpose.

## TODO
- Improve/verify institution code translations for all fields where used
- Improve parsing of lifespan dates and other fields from author column
- Improve publication place/year parsing from publication info column
- ~~Investigate ways of matching/aligning records with existing records imported from OCLC that contain `links` to HathiTrust pages~~