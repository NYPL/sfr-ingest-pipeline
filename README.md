# SFR Database Updater
This is a Lambda function that manages updating exsting records within postgres. This manages updates to records that currently *exist* within the database and which should be updated or overwritten in any way. These messages are received either from the sfr-db-manager or from Lambda functions further along in the ingest pipeline.

## Version
v0.0.1

## Deployment
This function should be deployed through an instance of Amazon's AMI, as that layer is necessary to properly compile several dependencies for the Lambda environment. This can be done either via an EC2 isntance deployed with the AMI or via a Docker container created via Amazon's Linux image.


## Environment Variables
This function can be configured to connect to a AWS RDS database running in the proper VPC

- LOG_LEVEL: Set the relevant log level (will appear in the cloudwatch logs)
- DB_HOST: Host of our Postgresql instance (within the VPC where this function is currently deployed)
- DB_PORT: Postgresql port on host above
- DB_NAME: Name of Postgresql database
- DB_USER: User for specified database
- DB_PASS: Password for above user

## Dependencies
- pyscopg2-binary
- pycountry
- pyyaml
- SQLAlchemy