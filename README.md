# SFR Database Core Layer

[![Build Status](https://travis-ci.com/NYPL/sfr-db-core.svg?branch=master)](https://travis-ci.com/NYPL/sfr-db-core)
[![GitHub version](https://badge.fury.io/gh/nypl%2Fsfr-db-core.svg)](https://badge.fury.io/gh/nypl%2Fsfr-db-core)

This package contains the scaffolding and ORM for the SFR database model. Included in this is the core `model`, defined as a SQLAlchemy ORM, db migrations managed by Alembic and a `SessionManager` class that handles record update operations. It is packaged as a Layer for the AWS Lambda service.

This allows various Lambda functions of the SFR ingest pipeline to share a unified database model and greatly simplify the process of updating and migrating the database.

## Version

v0.1.1

## Requirements

alembic
psycopg2-binary
pycountry
python-dateutil
requests
sqlalchemy

## Deployment

AWS Lambda functions a run in an environment based off of the Amazon's Linux image. This image does not include several libraries that are necessary to compile and run some Python libraries with C/C++ dependencies. To ensure that these dependencies are satisfied the library is built in a container that installs this package locally and uploads the resulting structure either as a new Layer or as a new version of an existing layer. This requires that `docker` be running. Deployment is a two step process

**Step 1**
From the `sfrCore` directory of this repository create a docker image with the command `docker build -t sfr_core_layer --build-arg accesskey=[AWS_ACCESS_KEY] --build-arg secretkey=[AWS_SECRET_KEY] --build-arg region=[AWS_REGION]`

This takes the following arguments:

- accesskey: The `access_key_id` for your AWS account
- secretkey: The `access_secret_key_id` for your AWS account
- region: The `region` that the layer will be deployed to

**Step 2**
Verify that the image was created with `docker images` and then run the container with `docker run -e GIT_URL=[GITHUB_EGG_URL] -e LAYER_NAME=[LAYER_NAME] sfr_core_layer` This will show the package being installed from Github, zipped and then deployed to AWS. Verify that the layer was either created or updated with a new version number in the AWS Console.

This step has two arguments:

- GIT_URL: A URL to the Github repository where this repository can be installed from. Different versions/releases can be installed by using the `@` modified. The URL should look like `git+[REPO_URL]@[version/tag/release]#egg=sfrCore` where the portion following the `@` could be `master`, `development` or `0.1.0`
- LAYER_NAME: The name that should be given to the layer in AWS. To create a new version of an existing layer provide the name of that layer here

## Database migrations

Migrations are handled with `alembic`, which needs to be configured before use. To do copy `alembic.ini.sample` to `alembic.ini` and edit the `sqlalchemy.url` line with a URL to the database instance in the form `postgresql://[DB_USER]:[DB_PSWD]@[DB_HOST]/[DB_NAME]`.

To create a new migration run `alembic revision -m "Migration description"` and then edit the newly created file in `alembic/versions`. To run this and migration and bring the database up to date run `alembic upgrade head`. If the database was cloned from another instance, it may be necessary to run `alembic stamp [most_recent_revision_#]` to mark the database instance as already incorporating these previous migrations.

## Development

To make improvements to the core model create a feature branch from `development` and create a PR to merge in these changes. Versioning should follow standard practices with breaking changes (mainly database migrations) constituting major releases. Improvements to model code should be considered a minor release if they do not impact overall functionality.

### TODO

- Add travisCI integration
- Migrate test suites from existing repositories
- Integrate linting standard