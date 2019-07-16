# SFR Search API

[![Build Status](https://travis-ci.com/NYPL/sfr-search-api.svg?branch=development)](https://travis-ci.com/NYPL/sfr-search-api)
[![GitHub version](https://badge.fury.io/gh/nypl%2Fsfr-search-api.svg)](https://badge.fury.io/gh/nypl%2Fsfr-search-api)

Provides access to the SFR ElasticSearch index. Currently supports basic search on `keyword`, `title`, `author` and `subject` fields, as well as single record retrieval by `identifier`.

View Swagger documentation for [v2](https://dev-platformdocs.nypl.org)

View the Endpoint descriptions in [Confluence](https://confluence.nypl.org/display/SFR/Search+API)

## Installing

Uses nvm to manage Node.js version.

1. Clone this repository
2. Run `npm install`
3. Copy the example environment variable file to .env at the root
4. Retrieve variable values from a colleague
5. Start via `npm start`

Environment variables for local configuration are encrypted. Use the procedure described by NYPL's Security policies in engineering-general.

## Git Workflow

`master` is the source branch

1. Cut a feature branch from master
2. Create pull request with reviewers against master
3. Merge pull request upon approval
4. Merge to the appropriate branch `qa` and/or `production`
5. Create a release tag
6. Deployment happens on successful merge to the appropriate environment branch

## Testing

Testing is available through `mocha` and can be run with `npm run test`. Currently implemented is a set of unit tests as well as a limited number of integration tests that verify the API's connection to an ElasticSearch cluster and the ability to return records from that cluster.

Linting is provided through the `standard` guide and is required. `npm run lint` will generate a linting report of any issues.

To start a local test instance run `npm run start-dev`.

## Deployment

Deployment is made to an ElasticBeanstalk instance and can be managed on the CLI with the python package `awsebcli`. Before deploying the eb environment needs to be initialized with `eb init`. If this code was previously deployed to an ElasticBeanstalk instance in your AWS account, this should be automatically detected and configured. Otherwise the CLI will prompt with the necessary steps.

After initialization, if this is a new application, run `eb create` to create the instance and deploy a new version of the application. If deploying to an existing instance run `eb deploy` to generate a new deployment package and push this to the instance.

## Searching

The `search` endpoint supports both `GET` and `POST` requests with the same basic parameters. Queries can be both for an individual term or an array of terms. In either case the main `query` object must be comprised of the following:

- `field` the field(s) you would like to search. Currently supported are `keyword`, `title`, `author` and `subject`.
- `query` the string you would like to search. The query field supports boolean search construction as well as quotation marks for exact term matching.

For example a simple search query looks like:

``` json
{
    "field": "keyword",
    "query": "history"
}
```

A more complex query looks like:"

``` json
{
    "queries": [
        {
            "field": "keyword",
            "query": "New York City"
        },{
            "field": "subject",
            "query": "history"
        }
    ]
}
```

### Search Fields

The following search field options are supported:

- `keyword`: The default search field that queries all fields associated with a work record. NOTE: this does not include authors or subjects.
- `author`: A full text search against author names. This search is restricted by agents' `roles` as they pertain to works and instances. For example this will return a work if an agent has a "contributor" relationship but not if they have a "publisher" relationship. These roles are filtered by a blacklist maintained in the `lib/search.js` file.
- `viaf`: An utility endpoint that returns works associated with an agent identified by a VIAF ID.
- `lcnaf`: An utility endpoint that returns works associated with a LCNAF ID.
- `subject`: Queries the full set of subjects associated with a work.

## Paging

ElasticSearch supports two distinct paging strategies, both of which are supported by this API. A standard `from/size` option allows for the retrieval of arbitrary pages in the index and a `search_after` option that allows for retrieval of adjacent records from a current result set. It should be noted that ElasticSearch, by default, restricts `from/size` to the first 10,000 records of a result set. This is circumvented internally by manipulating the result object.

The paging options are:

- `per_page` The total number of results to return.
- `page` The page of results to return. Can be used to return subsequent pages of results if a large number of results are returned.
- `next_page_sort` The `sort` object of the LAST `hit` in a results page. This used internally by Elastic to retrieve the next page of results
- `prev_page_sort` The `sort` object of the FIRST `hit` in a results page. Used internally to retrieve the previous page of results.
- `total` This is used to help retrieve an arbitrary page from a query. This is never required, but providing this as a parameter with a search request removes the need to calculate the size, speeding the response.

## Sorting

Basic sorting is implemented to support the requirements of the next/previous page functionality. The default sort is by the internal ElasticSearch scoring algorithm, based off the initial search query. This can be changed to any field in the index. Adding a sort involves placing a single parameter, `sort`, in the request, which is an array of objects with the following fields:

- `field` The field to sort the results on. The currently valid sorting options are:
  - title
  - author
  - date (This sorts on either the first or last publication date, depending on the sort direction)
- `dir` The direction of the sort, either `asc` or `desc`

## Filtering

Filtering is supported on a set of pre-defined fields. At present the following filters are supported:

- `language`: Filters results to return only works matching the provided language
- `years`: Filters results to return only works with publication dates based off the provided range. This is calculated from the publication dates associated with the editions for each work. This should be formatted as `{"start": year, "end": year}`.
- `show_all`: By default, the search results only include works with editions that have readable copies (either downloadable or available to read online). Setting this value to `true` will return all works, regardless of this status, in the search results.

## Aggregations/Facets

Aggregations provide the ability to narrow searches from a results page by providing options that can be browsed and selected. Aggregations blocks are returned by default with all search results and can be used to pass additional parameters
to a `filter` which can return a smaller result set. At present the following aggregation blocks are returned:

- `languages`: An array of languages with their frequency in the current, full, result set, sorted in descending order of frequency.

## Single Record

The `work` endpoint also supports both `GET` and `POST` requests and returns a single work from the SFR ElasticSearch instance. This accepts a single parameter in both methods: `identifier` which accepts an identifier and queries the SFR index for a single record. The `identifier` can be either an UUID or other identifier recognized by the SFR index such as an OCLC number, LCCN, ISBN, ISSN or other identifiers.

UUID is preferred as it is the only identifier that is guaranteed to only return a single record.

If no results or multiple results are found for an identifier, this will return a non-200 error message.

## Utilities

The API also supports a `utils` route that can provide additional functionality that supports the core functionality of the API. These endpoints will return statistics, specific pieces of data from the collection or other small functions that can help support large functionality. Each existing utility endpoint will be detailed in this section

### Language List: (`utils/languages`) [`GET`]

This endpoint returns a list of all languages that currently exist in the ResearchNow database. This allows the advanced search interface to present users with an array of all languages they might filter their results by. This accepts a single query parameter: `total` which accepts a boolean value (`false` by default) and which returns the total count of `Work` records associated with each language when enabled. This allows API users to quickly obtain a list of `Work` counts by language, enabling insights into the data and potential use as a visualization/feature.
