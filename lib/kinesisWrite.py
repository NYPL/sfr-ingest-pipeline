import json
import os

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
    def putRecord(cls, outputObject, stream):
        """Put an event into the specific Kinesis stream"""
        logger.info('Writing results to Kinesis')

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
                PartitionKey=os.environ['OUTPUT_SHARD']
            )
        except:  # noqa: E722
            logger.error('Kinesis Write error!')
            raise KinesisError('Failed to write result to output stream!')
