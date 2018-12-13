# OCLC Classify Enhancer (Step 1 of FRBR-ization)
This lambda takes a set of metadata conforming to the SFR Data Model (to be documented) and queries the [OCLC Classify](https://www.oclc.org/developer/develop/web-services/classify.en.html) for additional metadata pertaining to Works, Instances and Agents(Entities). This data is merged into the original metadata record and then passed on to the next stage in the enhancement pipeline.

The Classify service provides both basic Work level data (official title, identifiers and author/contributor information), as well as a full list of all potential editions that OCLC is aware of. This list of editions contains many possible duplicates, but those will be reduced/combined as necessary in future steps.

## Version
v0.0.1

## Note
This code is based on the [Python Lambda Boilerplate](https://github.com/NYPL/python-lambda-boilerplate), and as a result can be run through the `make` commands detailed there such as `make test` and `make local-run`

**Important** In order to function this needs several sensitive environment variables to be set in the relevant `config` file:
- OCLC_KEY: A valid OCLC API key
- OUTPUT_REGION: The region where your output Kinesis stream is deployed
- OUTPUT_KINESIS: The Kinesis stream to be written to
- OUTPUT_SHARD: The shard of the stream to be written to

## Input
Accepts a Metadata record generated either by harvesting records from one of the data contributors to the SFR project (such as Project Gutenberg) or from a newly digitized volume, and generating a Work record that can either be stored in the database or enhanced with further steps in a FRBR-ization process (such as with the OCLC Lookup service or other data normalization steps)

## Output
A **Work** record containing the following fields
- Title [String]
- SubTitle [String]
- AltTitles [Array]
- Source [String]
- Language [String]
- License [URI]
- Rights Statement [String]
- Issued [Datetime]
- Published [Datetime]
- Medium [String]
- Series [String]
- Series Position [String]
- Primary Identifier [Identifier Object]
- Identifiers [Array]
- Subjects [Array]
- Agents [Array]
- Instances [Array]
- Measurements [Array]
- Links [Array]


## ToDo

- Add further comments/tests to increase coverage
- Chaos test with various strange/incomplete/erroneous input metadata blocks
- Refactor matching code in several places where it could be cleaner/better
