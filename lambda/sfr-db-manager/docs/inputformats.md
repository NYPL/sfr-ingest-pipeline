# Input Formats
The database manager accepts record inputs from a variety of sources, but they must conform to both the data model and a common messaging format. For the input data, which is drawn from the SFR data sources or internal data services, this includes a data block with additional metadata fields that help with the parsing process.

## Generic Format
- Status: A standard status code reflecting the state of the incoming data block. Currently the following status codes are valid
  - 200: OK
  - 500: Error
- Message: A descriptive message describing the incoming message. Generally a statement about the retrieved data or a summary of the error if the status is non-200
- Source: The source of the incoming data. This will either be one of the data providers or an internal data pipeline that is processing existing data in some way
- Type: The type of data contained in this object. Valid types are
  - Work: A full work record representing an ebook
  - Instance: A specific edition or other version of an ebook, to be associated with an existing work
  - Item: A specific copy of an instance, to be associated with an existing instance. Items will generally be created by the epub storage pipeline
  - Access Report: An accessibility report generated for a stored copy of an ePub file. Associated with an item, the accessibility reports provide a general score for how accessible an individual item is.
- Method: This indicates whether the record is an `insert` operation where the function will test if a record exists and creates one if not. And an `update` operation that assumes a matching record already exists and updates that record
- Data: A field containing the record data, or in the case of the error, the full error message. This object must conform the data model as defined in this function.

## Example
```
{
  "status": 200,
  "message": "Retrieved Data from SOURCE",
  "source": "Input Source",
  "type": "work|instance|item",
  "method": "insert|update",
  "data": [Metadata Object]
}
```
