View Swagger documention for [v0.1](https://dev-platformdocs.nypl.org)

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

##Deployment

###ElasticBeanstalk

##Searching

##Filtering

##Aggregations

##Single Record
