# Gutenberg Ingest Lambda for ResearchNow
This lambda reads recently published/updated files from Project Gutenberg and processes them for the ResearchNow project.

## Process
This ingest process utilizes the GITenberg project (https://github.com/gitenberg) which maintains the Project Gutenberg collection as a set of repositories. It queries this collection via the GitHub GraphQL API and uses the returned RDF file to build a basic metadata profile of each volume. It is designed to be run nightly and get records updated
in the past 24 hours, but this can be adjusted to run as frequently (or infrequently) as necessary.

## Output
The lambda writes a basic metadata block to a Kinesis stream. That block includes:
- Title/Alt Title
- Publisher
- Created
- Updated
- Subjects
- ePub Formats
- Entities (creator, editor, etc.)

## TODO
- Create version of Lambda that can ingest ALL records
- ~~Write basic unit tests~~
- Add CI code/tests
- Better Documentation/Comment Coverage
