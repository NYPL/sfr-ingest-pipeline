# Ace Accessibility Report Service

This application generates accessibility reports and scores for `EPUB` files utilizing the ACE tool published by the Daisy Consortium. It reads messages from a `SQS` queue, which trigger report generation, with the completed reports placed in a Kinesis stream for ingest into the SFR persistent layer by the `sfr-db-manager` lambda function.

## Message Format
The `SQS` messages read by the application are relatively simple and consist of 3 fields:

- fileKey: An S3 key to an EPUB Zip Archive. This is the file that is to be parsed by the reporter
- identifier: The `postgresql ROWID` for the `Item` record that this report is to be associated with
- instanceID: The `ROWID` for the parent `Instance` of the `Item` the report is being associated with

### Example

``` JSON
{
  "fileKey": "path/to/epub/zip/archive",
  "identifier": "[integer]",
  "instanceID": "[integer]"
}
```

## Environment
This API can be deployed in an ec2 instance, and depending on the AMI used several dependencies may need to be installed/configured

- pm2 is used to daemonize the API. This should be installed and use to start/run the node app.
- Chromium is a dependency of the Ace Accessibility Report. npm will install this package but depending on the linux distro several dependencies may be missing. If that is the case you may need to install the libX libraries or others. It is difficult to predict. This can be partially solved by installing chromium via yum/apt-get which will pull in at least some of those dependencies if not all. **TODO** Create list of all necessary dependcies and include one-line install script here

### Setup Details

Further information on how/why this service is currently configured can be found in [the further documentation](docs/rationale.md)

### Tasks

- Create TravisCI integration that auto-deploys to an ec2 instance
- Create integration tests with other parts of ingest pipeline
- ~~Look at potential ways to decrease processing time without migrating to larger instance~~
