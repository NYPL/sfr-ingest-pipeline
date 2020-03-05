import hashlib
import json

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

    def __init__(self):
        pass

    @classmethod
    def putKinesis(cls, data, stream, recType='work'):
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

        # The default lambda function here converts all objects into dicts
        kinesisStream = OutputManager._convertToJSON(outputObject)

        partKey = OutputManager._createPartitionKey(data)

        try:
            cls.KINESIS_CLIENT.put_record(
                StreamName=stream,
                Data=kinesisStream,
                PartitionKey=partKey
            )

        except:  # noqa: E702
            logger.error('Kinesis Write error!')
            raise OutputError('Failed to write result to output stream!')

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
        md5 = hashlib.md5()
        md5.update(obj['storedURL'].encode('utf-8'))
        return md5.hexdigest()
