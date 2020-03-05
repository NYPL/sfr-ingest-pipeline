# ~~Output Format~~
The output format for the db-manager is deprecated. The output formerly pushed records to an SQS stream that provided UUIDs to be updated in ElasticSearch. This has been replaced by a more effecient time-based polling strategy and at present there is no final output from this function.
