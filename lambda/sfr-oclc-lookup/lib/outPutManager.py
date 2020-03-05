import boto3
import json
import datetime
import time

from helpers.errorHelpers import KinesisError
from helpers.logHelpers import createLog
from helpers.clientHelpers import createAWSClient

logger = createLog('kinesis_write')


class OutputManager():
    """Class for managing connections and operations with AWS Kinesis"""
    KINESIS_CLIENT = createAWSClient('kinesis')

    def __init__(self):
        pass

    @classmethod
    def putRecord(cls, outputObject, stream, workUUID):
        """Put an event into the specific Kinesis stream"""
        logger.info("Writing results to Kinesis")

        # The default lambda function here converts all objects into dicts
        kinesisStream = OutputManager._convertToJSON(outputObject)

        try:
            cls.KINESIS_CLIENT.put_record(
                StreamName=stream,
                Data=kinesisStream,
                PartitionKey=workUUID
            )
        except:
            logger.error('Kinesis Write error!')
            raise KinesisError('Failed to write result to output stream!')

    @staticmethod
    def _convertToJSON(obj):
        """Converts an object or dict to a JSON string.
        the DEFAULT parameter implements a lambda function to get the values
        from an object using the vars() builtin."""
        return json.dumps(obj, ensure_ascii=False, default=lambda x: vars(x))

    @staticmethod
    def formatResponse(status, data):
        """Creates a response block to be returned to the API client.
        Arguments:
            status {integer} -- A standard HTTP status code.
            data {dict} -- A dictionary containing either an error message or a
            set of metadata describing the agent being queried.
        Returns:
            [dict] -- A complete response object containing a status and
            relevant data.
        """
        return {
            'statusCode': status,
            'headers': {
                'req-time': time.time()
            },
            'isBase64Encoded': False,
            'body': OutputManager._convertToJSON(data)
        }
