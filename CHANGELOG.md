# Changelog
This file documents all updates and releases to the ResearchNow Data Ingest pipeline.

## [Unreleased]
### Fixed
- Improved identifier parsing for MET catalog

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
