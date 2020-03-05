# SFR Edition Clustering

This Lambda function processes `instance` records associated with an individual `work` and clusters them together in `edition` groups through the k-means clustering algorithm.

This process is intended to take metadata associated with OCLC records and others and attempt to identify "markers" of real-world editions. Frequently the data available to this project does not specifically identify an edition in the scope of a `work` (e.g. the 3rd edition, from New York in 1895 of 6 total editions, as opposed to a copy of an 1895 edition, with no surrounding context).

This script reads from a stream of SQS messages containing ResearchNow `work` UUIDs. Each of these records are processed with their related `instances` adding data to the `editions` table which relates to both the `work` and the related `instances`. This table holds a limited set of metadata but can access the full set of related metadata through these relationships.

## Requirements

Python 3.6+ (written with Python 3.7)

- elasticsearch-dsl==6.3.1 (for ElasticSearch-6.X.X installations)
- pandas
- scikit-learn

### Deployment Requirements

Due to restrictions on the total size of the upload package to AWS Lambda, and requirements of running python libraries that invoke C libraries in the Lambda environment, this function must deployed in a specific way.

The easiest way around these restrictions is to deploy the `pandas` and `scikit-learn` dependencies as lambda layers. In addition the official AWS layer that includes `numpy` and `scipy` can be used to include those dependencies. For
this function this means that the following layers should be included:

1) Official AWS Layer for `scipy` and `numpy`
2) Custom layer installing `pandas` and `scikit-learn`
3) Custom layer installing `sfrCore`

To invoke these layers the `PYTHONPATH` of the lambda function needs to be updated to `/opt/python:/opt/python/lib/python3.7/site-packages:$PYTHONPATH` to place the required libraries on the path

## Getting Started

### Installation

1. Create a virtualenv (varies depending on your shell) and activate it
2. Install dependencies via `pip install -r requirements.txt`
3. (Optional) Install dev dependencies via `pip install -r requirements.txt` for local development

### Setup Configurations

**Step 1**
After installing dependencies, copy the config.yaml.sample file to config.yaml and modify the relevant values. At a minimum the following settings should be changed:

- function_name
- description
- role

**Step 2**
Add environment specific variables in the `config` directory. `development.yaml/qa.yaml/production/yaml` for deployment environments and `local.yaml` for local testing variables.

*Important* When adding environment variables be sure to encode sensitive information with the AWS KMS encryption service. Decryption is supported by default in the `sfr-db-core` library that this is built with.

Required environment variables:

- LOG_LEVEL: Options: debug/info/warning/error
- PYTHONPATH: Provides AWS Lambda reference to included layers, by default should be `/opt/python`
- DB_HOST: Sensitive, should be encrypted
- DB_NAME: Sensitive, should be encrypted
- DB_USER: Sensitive, should be encrypted
- DB_PSWD: Sensitive, should be encrypted
- DB_PORT
- ES_HOST
- ES_PORT
- ES_TIMEOUT
- ES_INDEX

**Step 3**
Modify the included event.json to add to the Records block, which enables the Lambda to be tested locally. This function is designed to read SQS messages, and as such this should have the general format:

``` json
{
    "source": "SQS",
    "Records": [
        {
            "body": "{\"type\": \"uuid\", \"identifier\": \"test_uuid_here\"}"
        }
    ]
}
```

### Develop Locally

To run your lambda locally run `make local-run` which will execute the Lambda (initially outputting "Hello, World")

### Deploy the Lambda

To deploy the Lambda be sure that you have completed the setup steps above and have tested your lambda, as well as configured any necessary environment variables.

To run the deployment run `make deploy ENV=[environment]` where environment is one of development/qa/production

**Deploy via TravisCI**
This function is automatically deployed on merge through travisCI. This configuration can be found in the `.travis.yaml` file in this directory.

## Tests

`pytest` is currently used to provide test coverage and can be run with `make test`

`coverage` is used to measure test coverage and a report can be seen by running `make coverage-report`

## Linting

Linting is provided via Flake8 and can be run with `make lint`
