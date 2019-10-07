from io import BytesIO
import os

from helpers.logHelpers import createLog
from helpers.clientHelpers import createAWSClient


class s3Client:
    def __init__(self, s3Key):
        self.s3Client = createAWSClient('s3')
        self.key = s3Key
        self.bucket = os.environ.get('COVER_BUCKET', 'sfr-instance-covers')
        self.logger = createLog('s3Client')

    def checkForFile(self):
        try:
            self.s3Client.get_object(
                Bucket=self.bucket,
                Key=self.key,
                Range='bytes=0-0'
            )
            return self.returnS3URL()
        except self.s3Client.exceptions.NoSuchKey:
            self.logger.info('{} does not exist in {}'.format(
                self.key, self.bucket
            ))

        return None

    def storeNewFile(self, fileContents):
        self.s3Client.put_object(
            Bucket=self.bucket,
            Key=self.key,
            ACL='public-read',
            Body=BytesIO(fileContents).read()
        )
        return self.returnS3URL()

    def returnS3URL(self):
        return '{}.s3.amazonaws.com/{}'.format(
            self.bucket, self.key
        )
