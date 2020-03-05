# Ebook Ingest Message Format
When ingesting a work or instance record, the database manager will not directly import an epub (item) level record. It will instead pass that part of the record to a separate part of the pipeline that stores the epub file locally, generates an accessibility score and passes this data to a Kinesis stream.

This function passes data to start this process in the following format.

## Generic Format
- url: The url to the ebook file at its external source. This is the file to be stored locally.
- id: The id of the parent instance record. This will be used to associate the returned ebook data with the proper record.
- updated: A datetime string when the ebook was last updated by the source organization. This is used to determine if the ebook should be updated, or the existing local copy should be returned
- data: A raw block of the full item record
- size: The size of the ebook file in bytes

## Example
```
{
  "url": "http://sample.ebook.url",
  "id": "instance.id",
  "updated": "2018-12-31T12:00:00.0Z",
  "data": [Item Object],
  "size": "1000000"
}
```
