import yaml
import shutil
import os
import configparser

from helpers.logHelpers import createLog
from helpers.errorHelpers import InvalidExecutionType

logger = createLog('configHelpers')

def loadEnvFile(runType, fileString):

    envDict = None
    fileLines = []

    if fileString:
        openFile = fileString.format(runType)
    else:
        openFile = 'config.yaml'
        if os.path.isfile('run_config.yaml'):
            openFile = 'run_config.yaml'
    try:
        with open(openFile) as envStream:
            try:
                envDict = yaml.load(envStream)
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


def setEnvVars(runType):

    # Load env variables from relevant .yaml file
    envDict, envLines = loadEnvFile(runType, 'config/{}.yaml')

    # If no environemnt variables are set, do nothing to config
    if 'environment_variables' not in envDict:
        shutil.copyfile('config.yaml', 'run_config.yaml')
        return

    # Overwrite/add any vars in the core config.yaml file
    configDict, configLines = loadEnvFile(runType, None)

    envVars = configDict['environment_variables']
    for key, value in envDict['environment_variables'].items():
        envVars[key] = value

    newEnvVars = yaml.dump({
        'environment_variables': envVars
    }, default_flow_style=False)
    try:

        config = configparser.ConfigParser()
        try:
            config.read(os.path.expanduser('~/.aws/credentials'))
        except configparser.MissingSectionHeaderError:
            pass

        with open('run_config.yaml', 'w') as newConfig:
            write = True
            written = False
            for line in configLines:
                
                if line.strip() == 'aws_access_key_id:':
                    try:
                        keyID = os.environ['AWS_ACCESS_KEY_ID_DEVELOPMENT']
                    except KeyError:
                        keyID = config['default']['aws_access_key_id']
                    newConfig.write('aws_access_key_id: {}\n'.format(keyID))
                    continue
                
                if line.strip() == 'aws_secret_access_key:':
                    try:
                        awsKey = os.environ['AWS_SECRET_ACCESS_KEY_DEVELOPMENT']
                    except KeyError:
                        awsKey = config['default']['aws_secret_access_key']
                    newConfig.write('aws_secret_access_key: {}\n'.format(awsKey))
                    continue
                
                if line.strip() == '# === END_ENV_VARIABLES ===':
                    write = True

                if write is False and written is False:
                    newConfig.write(newEnvVars)
                    written = True
                elif write is True:
                    newConfig.write(line)

                if line.strip() == '# === START_ENV_VARIABLES ===':
                    write = False

    except IOError as err:
        logger.error(('Script lacks necessary permissions, '
                      'ensure user has permission to write to directory'))
        raise err
