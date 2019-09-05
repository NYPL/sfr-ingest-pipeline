from base64 import b64decode
from binascii import Error as base64Error
import boto3
from botocore.exceptions import ClientError
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..model.core import Base
from ..helpers import createLog


class SessionManager():
    def __init__(self, user=None, pswd=None, host=None, port=None, db=None):
        self.user = user if user else SessionManager.decryptEnvVar('DB_USER')
        self.pswd = pswd if pswd else SessionManager.decryptEnvVar('DB_PSWD')
        self.host = host if host else SessionManager.decryptEnvVar('DB_HOST')
        self.port = port if port else SessionManager.decryptEnvVar('DB_PORT')
        self.db = db if db else SessionManager.decryptEnvVar('DB_NAME')

        self.engine = None
        self.session = None

        self.logger = createLog('dbManager')

    def generateEngine(self):
        try:
            self.engine = create_engine(
                'postgresql://{}:{}@{}:{}/{}'.format(
                    self.user,
                    self.pswd,
                    self.host,
                    self.port,
                    self.db
                )
            )
        except Exception as e:
            self.logger.error(e)
            raise e

    def initializeDatabase(self):
        if not self.engine.dialect.has_table(self.engine, 'works'):
            Base.metadata.create_all(self.engine)

    def createSession(self, autoflush=True):
        if not self.engine:
            self.generateEngine()
        self.session = sessionmaker(bind=self.engine, autoflush=autoflush)()
        return self.session

    def startSession(self):
        self.session.begin_nested()

    def commitChanges(self):
        self.session.commit()

    def rollbackChanges(self):
        self.session.rollback()

    def closeConnection(self):
        self.commitChanges()
        self.session.close()
        self.engine.dispose()

    @staticmethod
    def decryptEnvVar(envVar):
        encrypted = os.environ.get(envVar, None)

        try:
            decoded = b64decode(encrypted)
        except (TypeError, base64Error):
            return encrypted

        try:
            return boto3.client('kms')\
                .decrypt(CiphertextBlob=decoded)['Plaintext'].decode('utf-8')
        except (ClientError, TypeError):
            return decoded.decode('utf-8')
