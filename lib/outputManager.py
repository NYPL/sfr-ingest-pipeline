import json
import os

from helpers.errorHelpers import OutputError
from helpers.logHelpers import createLog
from helpers.clientHelpers import createAWSClient

logger = createLog('output_write')


class OutputManager():
    """Controls the output formats and streams from this function. Valid output
    targets are:
    Kinesis: for processing in the enhancement pipeline and epub storage
    SQS: For queuing and processing by the ElasticSearch manager"""

    KINESIS_CLIENT = createAWSClient('kinesis')
    SQS_CLIENT = createAWSClient('sqs')

    def __init__(self):
        pass

    @classmethod
    def putKinesis(cls, data, stream):
        """Puts records into a Kinesis stream for processing by other parts of
        the SFR data pipeline. Takes data as an object and converts it into a
        JSON string. This is then passed to the specified stream.

        This will raise any error, as failure to pass an output should halt the
        process."""

        logger.info('Writing results to Kinesis')
        outputObject = {
            'status': 200,
            'data': data
        }

        # The default lambda function here converts all objects into dicts
        kinesisStream = OutputManager._convertToJSON(outputObject)

        try:
            cls.KINESIS_CLIENT.put_record(
                StreamName=stream,
                Data=kinesisStream,
                PartitionKey='0'
            )

        except:
            logger.error('Kinesis Write error!')
            raise OutputError('Failed to write result to output stream!')

    @classmethod
    def putQueue(cls, data):
        """This puts record identifiers into an SQS queue that is read for
        records to (re)index in ElasticSearch. Takes an object which is
        converted into a JSON string."""

        logger.info('Writing results to SQS')
        outputObject = {
            'type': data['type'],
            'identifier': data['identifier']
        }
        # The default lambda function here converts all objects into dicts
        messageData = OutputManager._convertToJSON(outputObject)

        try:
            cls.SQS_CLIENT.send_message(
                QueueUrl=os.environ['OUTPUT_SQS'],
                MessageBody=messageData
            )
        except:
            logger.error('SQS Write error!')
            raise OutputError('Failed to write result to output stream!')

    @staticmethod
    def _convertToJSON(obj):
        """Converts an object or dict to a JSON string.
        the DEFAULT parameter implements a lambda function to get the values
        from an object using the vars() builtin."""
        return json.dumps(obj, ensure_ascii=False, default=lambda x: vars(x))
