# Ace Accessibility Report API Service
This is a basic Express server that generate Accessiblity reports for ePub files using the Daisy Ace library. It comprises part of the ResearchNow data ingest pipeline

## Endpoints

**/ (GET)** A basic status endpoint that should just return a 200 status message if the API is running

**/generate_report (POST)** This generates the Accessibility report. It takes one parameter, a simple json block containing a Buffer of the data from an .epub archive file. It should be:
`
{
  {
    'type': 'Buffer',
    'data': [34, 54, 123, ...]
  }
}
`

## Environment
This API can be deployed in an ec2 instance, and depending on the AMI used several dependencies may need to be installed/configured
- NGINX is used as a reverse proxy. This should be installed and configured to proxy requests to port 3000
- pm2 is used to daemonize the API. This should be installed and use to start/run the node app.
- Chromium is a dependency of the Ace Accessibility Report. npm will install this package but depending on the linux distro several dependencies may be missing. If that is the case you may need to install the libX libraries or others. It is difficult to predict. This can be partially solved by installing chromium via yum/apt-get which will pull in at least some of those dependencies if not all. **TODO** Create list of all necessary dependcies and include one-line install script here

### Tasks
- Create TravisCI integration that auto-deploys to an ec2 instance
- Create integration tests with other parts of ingest pipeline
- Look at potential ways to decrease processing time without migrating to larger instance
