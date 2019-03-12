# SFR Search API
Provides access to the SFR ElasticSearch index. Currently supports basic search on `keyword`, `title`, `author` and `subject` fields, as well as single record retrieval by `identifier`.

View Swagger documention for [v2](https://dev-platformdocs.nypl.org)

##Installing
Uses nvm to manage Node.js version.

1. Clone this repository
2. Run `npm install`
3. Copy the example environment variable file to .env at the root
4. Retrieve variable values from a colleague
5. Start via `npm start`

Environment variables for local configuration are encrypted. Use the procedure described by NYPL's Security policies in engineering-general.

##Git Workflow

`master` is the source branch

1. Cut a feature branch from master
2. Create pull request with reviewers against master
3. Merge pull request upon approval
4. Merge to the appropriate branch `qa` and/or `production`
5. Create a release tag
6. Deployment happens on successful merge to the appropriate environment branch

##Testing

Testing is available through `mocha` and can be run with `npm run test`. Currently implemented is a set of unit tests as well as a limited number of integration tests that verify the API's connection to an ElasticSearch cluster and the ability to return records from that cluster.

Linting is provided through the `standard` guide and is required. `npm run lint` will generate a linting report of any issues.

To start a local test instance run `npm run start-dev`.

##Deployment

Deployment is made to an ElasticBeanstalk instance and can be managed on the CLI with the python package `awsebcli`. Before deploying the eb environment needs to be initialized with `eb init`. If this code was previously deployed to an ElasticBeanstalk instance in your AWS account, this should be automatically detected and configured. Otherwise the CLI will prompt with the necessary steps.

After initialization, if this is a new application, run `eb create` to create the instance and deploy a new version of the application. If deploying to an existing instance run `eb deploy` to generate a new deployment package and push this to the instance.

##Searching

The `search` endpoint supports both `GET` and `POST` requests with the same basic parameters. Required are:
 - `field` the field(s) you would like to search. Currently supported are `keyword`, `title`, `author` and `subject`.
 - `query` the string you would like to search. The query field supports boolean search construction as well as quotation marks for exact term matching.

 Additionally two optional parameters are supported:
 - `per_page` the total number of results to return
 - `page` the page of results to return. Can be used to return subsequent pages of results if a large number of results are returned.

##Filtering

TKTKTK

##Aggregations

TKTKTK

##Single Record

The `work` endpoint also supports both `GET` and `POST` requests and returns a single work from the SFR ElasticSearch instance. This accepts a single parameter in both methods: `identifier` which accepts an identifier and queries the SFR index for a single record. The `identifier` can be either an UUID or other identifier recognized by the SFR index such as an OCLC number, LCCN, ISBN, ISSN or other identifiers. 

If no results or multiple results are found for an identifier, this will return a non-200 error message.