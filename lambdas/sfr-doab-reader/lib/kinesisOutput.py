import json
import os
from pprint import pprint

from helpers.errorHelpers import KinesisError
from helpers.logHelpers import createLog
from helpers.clientHelpers import createAWSClient

logger = createLog('kinesis_write')


class KinesisOutput():
    """Class for managing connections and operations with AWS Kinesis"""
    KINESIS_CLIENT = createAWSClient('kinesis')

    def __init__(self):
        pass

    @classmethod
    def putRecord(cls, outputObject, stream, doabID):
        """Put an event into the specific Kinesis stream"""
        logger.info('Writing results to Kinesis {}'.format(stream))

        # The default lambda function here converts all objects into dicts
        kinesisStream = json.dumps(
            outputObject,
            ensure_ascii=False,
            default=lambda x: vars(x)
        )
        
        try:
            cls.KINESIS_CLIENT.put_record(
                StreamName=stream,
                Data=kinesisStream,
                PartitionKey=doabID
            )
        except:
            logger.error('Kinesis Write error!')
            raise KinesisError('Failed to write result to output stream!')