import boto3
import json
import datetime
import os

from helpers.errorHelpers import KinesisError
from helpers.logHelpers import createLog
from helpers.clientHelpers import createAWSClient

logger = createLog('kinesis_write')

class KinesisOutput():
    KINESIS_CLIENT = createAWSClient('kinesis')

    def __init__(self):
        pass

    @classmethod
    def putRecord(cls, record):

        logger.info("Writing results to Kinesis")
        outputObject = {
            'status': 200,
            'stage': os.environ['OUTPUT_STAGE'],
            'data': record
        }
        # The default lambda function here converts all objects into dicts
        kinesisStream = json.dumps(
            outputObject,
            ensure_ascii=False,
            default=lambda x: vars(x)
        )
        try:
            kinesisResp = cls.KINESIS_CLIENT.put_record(
                StreamName=os.environ['OUTPUT_KINESIS'],
                Data=kinesisStream,
                PartitionKey=os.environ['OUTPUT_SHARD']
            )
        except:
            logger.error('Kinesis Write error!')
            raise KinesisError('Failed to write result to output stream!')
