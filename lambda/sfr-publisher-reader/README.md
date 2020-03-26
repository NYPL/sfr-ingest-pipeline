# SFR Publisher Direct Ebook Ingest

Many smaller projects and publishers make open access and/or public domain eBooks available through their websites, but do not include these records in the larger aggregation projects that our projects draws the bulk of its records from.

This function provides a framework for writing custom importers for these sources, allowing us to gather and include these projects. This utilizes a basic plugin framework that incoprorates a reader and model for each source, ensuring that standard records are produced that can be passed to the ingest pipeline.

At present the following projects are supported

- MET Meseum Exhibiton Catalogs: This is a collection of the Metropolitan Museum of Arts digitized exhibiton catalogs. Some materials are released as open access and those produced before 1924 are in the public domain.

## Requirements

- Python 3.6+ (written with Python 3.7)

## Dependencies

- boto3
- pycountry
- requests

## Development

To develop this function, clone the `sfr-project` repository and follow the instructions for configuring that environment.

To add additional sources follow these steps:

1. Create a reader based an the `AbsSourceReader` (see existing readers for examples)
2. Implement an object model if necessary (if the source data is complex or requires a large amount of manipulation to fit into the SFR data model)
3. Add the new reader class as an `import` in the `__init__` file for the `readers` module and add it as an `ACTIVE_READER` in the relevant configuration files
4. Follow the instructions below for testing and running your reader

### Installation

Follow the instructions for installing the parent `sfr-project` repository

### Setup Environment Variables

The following environment variables should be set on a per-environment basis.

- LOG_LEVEL: One of `debug|info|warning|error`
- UPDATE_PERIOD: Period, in seconds, to check for updated instance records
- KINESIS_INGEST_STREAM: For development and production deployments this should be set to the AWS stream that feeds the `sfr-db-manager` function. For local deployments it can be an address of a local stream.
- ACTIVE_READERS: A comma-delimited stream of readers to to use in the import process. Allows for deactivation of projects that may not be actively updating records

### Develop Locally

To run this function locally run `make local-run` which will execute the Lambda. Use caution with this command, as configured it will place any fetched covers in the ingest stream for SFR, with potentially unintended side effects

### Deploy the Lambda

To deploy the Lambda be sure that you have completed the setup steps above and have tested your lambda, as well as configured any necessary environment variables.

To run the deployment run `make deploy ENV=[environment]` where environment is one of development/qa/production

## Tests

`pytest` is currently used to provide test coverage and can be run with `make test`

Coverage is used to measure test coverage and a report can be seen by running `make coverage-report`

## Linting

Linting is provided via Flake8 and can be run with `make lint`
