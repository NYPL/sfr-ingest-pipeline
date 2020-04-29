# Changelog
This file documents all updates and releases to the ResearchNow Data Ingest pipeline.

## [0.0.5] - Unreleased
### Added
- Edition detail endpoint to the API to allow users to retrieve an individual edition and its component instances
- Added identifier array to edition detail endpoint
- travisCI deployment for search API
- Add standardNumber option to search endpoint to query ISBN, ISSN, LCCN and OCLC; either individually or all together. Conforms to other search options
- Add `showAll` parameter to Work Detail endpoint to restrict return of editions/instances to only those with read online/download options
### Fixed
- Conform edition detail fields to other endpoints
- Add work UUID to edition detail response

## [0.0.4] - 2020-04-16
### Added
- New Reader for Internet Archive collections in the sfr-publisher-reader function
- Additional condition for Internet Archive covers in the s3 cover writer function
### Fixed
- Improved identifier parsing for MET catalog
- Fix bug in OCLC Catalog lookup to ensure that proper identifiers are fetched from records in the MARC 856 field
- Bug fix for error catching from the calendar module when parsing YYYY-MM or YYYY-YY date ranges

## [0.0.3] - 2020-04-01
### Added
- Publisher data reader to fetch metadata records from smaller projects. Initially this only includes the MET Exhibition Catalogs project.
- Parser for de Gruyter links for the `sfr-doab-reader`
### Fixed
- Refactored `sfr-doab-reader` tests
- Refactored `sfr-doab-reader` link parser loading to handle increasing number of parsers

## [0.0.2] - 2020-03-09
### Added
- Travis Integration to run tests across repository
- Exception raising in shell script to run test
### Fixed
- Improved test suite for number of components

## [0.0.1] - 2020-03-04
### Added
- This CHANGELOG file & the project's README
- The merged repositories from the previous multirepo environment
