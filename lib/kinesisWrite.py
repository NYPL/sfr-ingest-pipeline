import boto3
import json
import datetime
import os

from helpers.errorHelpers import KinesisError
from helpers.logHelpers import createLog

logger = createLog('kinesis_write')

class KinesisOutput():
    KINESIS_CLIENT = boto3.client(
        'kinesis',
        region_name = os.environ['OUTPUT_REGION']
    )

    def __init__(self):
        pass

    @classmethod
    def putRecord(cls, record):

        logger.info("Writing results to Kinesis")
        outputObject = {
            'status': 200,
            'stage': 'oclc-lookup',
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
