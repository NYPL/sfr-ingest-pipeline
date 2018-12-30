import json
import os

from helpers.errorHelpers import OutputError
from helpers.logHelpers import createLog
from helpers.clientHelpers import createAWSClient

logger = createLog('output_write')


class OutputManager():
    KINESIS_CLIENT = createAWSClient('kinesis')
    SQS_CLIENT = createAWSClient('sqs')

    def __init__(self):
        pass

    @classmethod
    def putKinesis(cls, data, stream):

        logger.info('Writing results to Kinesis')
        outputObject = {
            'status': 200,
            'data': data
        }
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
                PartitionKey='0'
            )

        except:
            logger.error('Kinesis Write error!')
            raise OutputError('Failed to write result to output stream!')

    @classmethod
    def putQueue(cls, data):

        logger.info('Writing results to SQS')
        outputObject = {
            'type': data['type'],
            'identifier': data['identifier']
        }
        # The default lambda function here converts all objects into dicts
        messageData = json.dumps(
            outputObject,
            ensure_ascii=False,
            default=lambda x: vars(x)
        )
        try:
            cls.SQS_CLIENT.send_message(
                QueueUrl=os.environ['OUTPUT_SQS'],
                MessageBody=messageData
            )
        except:
            logger.error('SQS Write error!')
            raise OutputError('Failed to write result to output stream!')
