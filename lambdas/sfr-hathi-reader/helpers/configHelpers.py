from base64 import b64decode
from binascii import Error as base64Error
import boto3
from botocore.exceptions import ClientError
import os
import yaml

from helpers.logHelpers import createLog


logger = createLog('configHelpers')


def loadEnvFile(runType, fileString):

    envDict = None
    fileLines = []

    if fileString:
        openFile = fileString.format(runType)
    else:
        openFile = 'config.yaml'

    try:
        with open(openFile) as envStream:
            try:
                envDict = yaml.safe_load(envStream)
            except yaml.YAMLError as err:
                logger.error('{} Invalid! Please review'.format(openFile))
                raise err

            envStream.seek(0)
            fileLines = envStream.readlines()

    except FileNotFoundError as err:
        logger.info('Missing config YAML file! Check directory')
        logger.debug(err)

    if envDict is None:
        envDict = {}
    return envDict, fileLines


def decryptEnvVar(envVar):
    """This helper method takes a KMS encoded environment variable and decrypts
    it into a usable value. Sensitive variables should be so encoded so that
    they can be stored in git and used in a CI/CD environment.
    Arguments:
        envVar {string} -- a string, either plaintext or a base64, encrypted
        value
    """
    encrypted = os.environ.get(envVar, None)

    try:
        decoded = b64decode(encrypted)
        # If region is not set, assume us-east-1
        regionName = os.environ.get('AWS_REGION', 'us-east-1')
        return boto3.client('kms', region_name=regionName)\
            .decrypt(CiphertextBlob=decoded)['Plaintext'].decode('utf-8')
    except (ClientError, base64Error, TypeError):
        return encrypted
