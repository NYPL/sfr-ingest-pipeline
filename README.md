# ResearchNow Book Cover s3 Storage

[![GitHub version](https://badge.fury.io/gh/nypl%2Fsfr-covers-to-s3.svg)](https://badge.fury.io/gh/nypl%2Fsfr-covers-to-s3) [![Build Status](https://travis-ci.com/NYPL/sfr-covers-to-s3.svg?branch=development)](https://travis-ci.com/NYPL/sfr-covers-to-s3)

## Summary

This lambda function reads from a SQS queue of image URLs that correspond to cover images for instance records from the ResearchNow data pipeline. It takes these original URLs, stores the image files in an s3 bucket and returns the resulting URL to the update Kinesis stream where the new URL will be stored in the database.

The files are stored in the designated bucket with a unique identifier generated from three components: the cover's filename, the name of the source and the identifier of the instance record it is to be associated with. The covers are organized by source.

These covers will be displayed on the search results and work detail pages in ResearchNow.

## Requirements

- Python 3.6+ (written with Python 3.7)
- AWS Credentials
- s3 Bucket
- SQS Queue

## Dependencies

- boto3
- coverage
- flake8
- pytest
- pytest-mock
- python-lambda
- pyyaml
- requests

## Installation

1. Create a virtualenv (varies depending on your shell) and activate it
2. Install dependencies via `pip install -r requirements.txt`
3. Install dev-dependencies via `pip install -r dev-requirements.txt`

## Usage

### Standard

This function should be deployed to AWS with a SQS queue as the event source. The function expects messages in this queue to have the following fields:

- `url`: An image URL that resolves to a `JPG` or `PNG` image
- `source`: The source of the image
- `identifier`: A unique identifier to the `instance` record this cover image will be associated with

It will create an image file in the specified bucket and return an object contaning both the original, remote, URL and the newly generated s3 URL, which will be written to a Kinesis stream.

### Local

To run this function locally (for testing or evaluation purposes) the an `event.json` file can be placed in the root directory with the following format:

``` json
{
    "source": "SQS",
    "Records": [{
        "body": "{\"url\": \"test_url\", \"source\": \"test_source\", \"identifier\": \"test_id\"}"
    }]
}
```

Once in place the test event (or events if configured), can be processed with `make run-local`

## Tests

Tests are run with `pytest` and can be run with `make test`

`coverage` is used to measure test coverage and a report can be seen by running `make coverage-report`

## Linting

Linting is provided via `flake8` and can be run with `make lint`

## Deployment

Deployment can be automated through `travisCI`, but requires adding AWS credentials as encrypted variables to the `.travis.yml` file. To deploy directly from your local environment to AWS, simply run `AWS deploy ENV=[desired_env]`. Recognized options are development|qa|production.
