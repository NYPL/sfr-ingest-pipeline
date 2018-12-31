# Output Format
The function ouputs record identifiers to an SQS stream. These records are then queued for indexing in ElasticSearch. This messaging format is drastically simpler than the input format as it only needs to identify the records to be updated.

At present anytime any part of a record is updated, we update the whole record in ElasticSearch, so the only identifier passed through at this time is the UUID used to uniquely identify each work record.

## Output Fields
- Type: The type of record being updated. At present we are only allowing updates of work records (Which necessarily contains updates to all of that work's children records)
- Identifier: The identifier of the record to update in the ElasticSearch index. Currently only work UUIDs are accepted by the indexer

## Example
```
{
  "type": "work",
  "identifier": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
}
```
