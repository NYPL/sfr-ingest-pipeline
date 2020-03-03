import json
import os
import redis
from datetime import datetime, timedelta

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
    AWS_REDIS = createAWSClient('elasticache')
    REDIS_CLIENT = redis.Redis(
        host=os.environ['REDIS_HOST'],
        port=6379,
        socket_timeout=5
    )

    def __init__(self):
        pass

    @classmethod
    def putKinesis(cls, data, stream, recType='work', attempts=None):
        """Puts records into a Kinesis stream for processing by other parts of
        the SFR data pipeline. Takes data as an object and converts it into a
        JSON string. This is then passed to the specified stream.

        This will raise any error, as failure to pass an output should halt the
        process."""

        logger.info('Writing results to Kinesis')
        outputObject = {
            'status': 200,
            'data': data,
            'type': recType
        }
        if attempts is not None:
            outputObject['attempts'] = attempts

        # The default lambda function here converts all objects into dicts
        kinesisStream = OutputManager._convertToJSON(outputObject)

        partKey = OutputManager._createPartitionKey(data)

        try:
            cls.KINESIS_CLIENT.put_record(
                StreamName=stream,
                Data=kinesisStream,
                PartitionKey=partKey
            )

        except:  # noqa: E722
            logger.error('Kinesis Write error!')
            raise OutputError('Failed to write result to output stream!')

    @classmethod
    def putKinesisBatch(cls, records, stream):
        streamRecords = [
            {
                'Data': OutputManager._convertToJSON(
                    {
                        'status': 200,
                        'data': r['data'],
                        'type': r['recType'],
                        'attempts': r.get('attempts', 0)
                    }
                ),
                'PartitionKey': OutputManager._createPartitionKey(r['data'])
            }
            for r in records
        ]

        try:
            cls.KINESIS_CLIENT.put_records(
                Records=streamRecords,
                StreamName=stream
            )
        except Exception as err:
            logger.error('Kinesis Batch write error')
            logger.debug(err)
            raise OutputError('Failed to write batch to Kinesis')

    @classmethod
    def putQueue(cls, data, outQueue):
        """This puts record identifiers into an SQS queue that is read for
        records to (re)index in ElasticSearch. Takes an object which is
        converted into a JSON string."""

        logger.info('Writing results to SQS')

        # The default lambda function here converts all objects into dicts
        messageData = OutputManager._convertToJSON(data)

        try:
            cls.SQS_CLIENT.send_message(
                QueueUrl=outQueue,
                MessageBody=messageData
            )
        except:  # noqa: E722
            logger.error('SQS Write error!')
            raise OutputError('Failed to write result to output stream!')

    @classmethod
    def putQueueBatches(cls, messages, outQueue):
        while len(messages) > 0:
            jsonMessages = []
            for i in range(10):
                try:
                    jsonMessages.append({
                        'MessageBody': OutputManager._convertToJSON(
                            messages.pop()
                        ),
                        'Id': str(i)
                    })
                except IndexError:
                    break

            try:
                cls.SQS_CLIENT.send_message_batch(
                    QueueUrl=outQueue,
                    Entries=jsonMessages
                )
            except Exception as err:
                logger.error('Failed to write messages to queue')
                logger.debug(err)
                raise OutputError('Failed to write results to queue')

    @classmethod
    def checkRecentQueries(cls, queryString):
        queryTime = cls.REDIS_CLIENT.get(queryString)
        logger.debug('Checking query recency of {} at {}'.format(
            queryString,
            queryTime
        ))
        currentTime = datetime.utcnow() - timedelta(days=1)
        if (
            queryTime is not None and
            datetime.strptime(
                queryTime.decode('utf-8'), '%Y-%m-%dT%H:%M:%S'
            ) >= currentTime
        ):
            return True

        cls.REDIS_CLIENT.set(
            queryString,
            datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
            ex=60*60*24*7
        )
        return False

    @staticmethod
    def _convertToJSON(obj):
        """Converts an object or dict to a JSON string.
        the DEFAULT parameter implements a lambda function to get the values
        from an object using the vars() builtin."""
        try:
            jsonStr = json.dumps(
                obj,
                ensure_ascii=False,
                default=lambda x: vars(x)
            )
        except TypeError:
            jsonStr = json.dumps(obj, ensure_ascii=False)

        return jsonStr

    @staticmethod
    def _createPartitionKey(obj):
        try:
            return str(obj['primary_identifier']['identifier'])
        except KeyError:
            pass

        try:
            return str(obj['identifiers'][0]['identifier'])
        except KeyError:
            pass

        try:
            return str(obj['id'])
        except KeyError:
            pass

        return '0'
