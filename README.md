# SFR VIAF Lookup

[![Build Status](https://travis-ci.com/NYPL/sfr-viaf-lookup.svg?token=Fv4twsPZbkerqgdJB89v&branch=development)](https://travis-ci.com/NYPL/sfr-viaf-lookup)

This function queries the OCLC VIAF API service to retrieve both controlled version of agent (individual and organizational) names and VIAF/LCNAF identifiers. This metadata is used to achieve more accurate matches of agent records within the SFR database and to improve performance by eliminating the need to do computationally expensive lookups within the `agent` table of the SFR database (specifically eliminating the need for fuzzy string matching queries)

This uses the [OCLC VIAF API](https://platform.worldcat.org/api-explorer/apis/VIAF), specifically the `Auto Suggest` endpoint, which returns a ranked set of `JSON` records containing basic metadata describing agent records. When a match is found, the result is both returned to the requesting service and cached in a `redis` cluster, which increases response times for the same query in the future by 10x.

The function is intended to be invoked by the AWS API Gateway and is configured to meet the request/response standards for that service.

## Version

v0.2.0

## Requirements

- pyyaml
- redis
- requests

## Installation

1. OPTIONAL - Create a virtualenv (varies depending on your shell) and activate it
2. Install dependencies via `pip install -r requirements.txt`
3. Create a test event in a file `event.json` with the format shown below
4. Run created test event with `make run-local`

### Sample event format

``` json
{
  "httpMethod": "GET",
  "queryStringParameters": {
    "queryName": "[agent_name_here]",
    "queryType": "[personal(DEFAULT)|corporate]"
  }
}
```

### Deploy the Lambda

To deploy the Lambda be sure that you have completed the setup steps above and have tested your lambda, as well as configured any necessary environment variables.

To run the deployment run `make deploy ENV=[environment]` where environment is one of development/qa/production

**Deploy via TravisCI**
This function will be automatically deployed when changes are pushed to the `development` or `production` branches via the settings defined in the `.travis.yml` file.

## Tests

The stock python `unittest` is currently used to provide test coverage and can be run with `make test`

Coverage is used to measure test coverage and a report can be seen by running `make coverage-report`

## Linting

Linting is provided via Flake8 and can be run with `make lint`
