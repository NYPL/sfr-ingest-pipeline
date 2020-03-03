# SFR Unglue.it Data Retrieval

[![Build Status](https://travis-ci.com/NYPL/sfr-unglueit-lookup.svg?branch=master)](https://travis-ci.com/NYPL/sfr-unglueit-lookup)

[![GitHub version](https://badge.fury.io/gh/sfr-unglueit-lookup.svg)](https://badge.fury.io/gh/sfr-unglueit-lookup)

This function queries the unglue.it API for metadata relating to ISBN numbers. This allows unique metadata from unglue.it, which is currently limited to summaries, to fetched for supplied ISBNs and associated with Work/Instance records within the ResearchNow database.

This function is invoked when an ISBN is received/added to an Instance record. It then retrieves a summary if available and adds it to the source record. This is done through the AWS API Gateway, where a custom endpoint exists for executing this query.

## Requirements

- lxml
- pyyaml
- requests

## Installation

1. OPTIONAL - Create a virtualenv (varies depending on your shell and activate it
2. Install dependencies via `pip install -r requirements.txt`
3. Create a test event in a file `event.json` with the format shown below
4. Run created test event with `make run-local`

To develop this function locally, the following steps can then be executed:

5. Install development dependencies with `pip install -r dev-requirements.txt`
6. Run tests and linting as described below

### Sample event format

``` json
{
  "httpMethod": "GET",
  "queryStringParameters": {
    "isbn": "[isbn_number]"
  }
}
```

### Deploy the Lambda

To deploy the Lambda be sure that you have completed the setup steps above and have tested your lambda, as well as configured any necessary environment variables.

To run the deployment run `make deploy ENV=[environment]` where environment is one of development/qa/production

**Deploy via TravisCI**
This function will be automatically deployed when changes are pushed to the `development` or `master` branches via the settings defined in the `.travis.yml` file.

## Tests

The stock python `unittest` is currently used to provide test coverage and can be run with `make test`

Coverage is used to measure test coverage and a report can be seen by running `make coverage-report`

## Linting

Linting is provided via Flake8 and can be run with `make lint`
