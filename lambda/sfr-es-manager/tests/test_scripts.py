import unittest
from unittest.mock import patch, mock_open, call
import logging
import pytest
from yaml import YAMLError
import json
import sys

from scripts.lambdaRun import main, setEnvVars, createEventMapping, loadEnvFile, createAWSClient  # noqa: E501
from helpers.errorHelpers import InvalidExecutionType

# Disable logging while we are running tests
logging.disable(logging.CRITICAL)


class TestScripts:
    @patch.object(sys, 'argv', ['make', 'development'])
    @patch('scripts.lambdaRun.setEnvVars')
    @patch('scripts.lambdaRun.createEventMapping')
    @patch('subprocess.run')
    @patch('os.remove')
    def test_run_deploy(self, mock_rm, mock_run, mock_env, mock_envVars):
        main()
        mock_envVars.assert_called_once()
        mock_env.assert_called_once()
        mock_run.assert_called_once()
        mock_rm.assert_called_once()

    @patch.object(sys, 'argv', ['make', 'run-local'])
    @patch('scripts.lambdaRun.setEnvVars')
    @patch('subprocess.run')
    @patch('os.remove')
    def test_run_local(self, mock_rm, mock_run, mock_envVars):
        main()
        mock_envVars.assert_called_once_with('local')
        mock_run.assert_called_once()
        mock_rm.assert_called_once_with('run_config.yaml')

    @patch.object(sys, 'argv', ['make', 'build-development'])
    @patch('scripts.lambdaRun.setEnvVars')
    @patch('subprocess.run')
    @patch('os.remove')
    def test_run_build(self, mock_rm, mock_run, mock_envVars):
        main()
        mock_envVars.assert_called_once_with('development')
        mock_run.assert_called_once()
        mock_rm.assert_called_once_with('run_config.yaml')

    @patch.object(sys, 'argv', ['make', 'bad-command'])
    def test_run_invalid(self):
        with pytest.raises(InvalidExecutionType):
            main()

    @patch.object(sys, 'argv', ['make', 'hello', 'jerry'])
    def test_run_surplus_argv(self):
        with pytest.raises(SystemExit):
            main()

    mockReturns = [
        ({
            'environment_variables': {
                'test': 'world'
            }
        }, ['region: Mesa Blanca', 'host: Rozelle']),
        ({
            'environment_variables': {
                'test': 'hello',
                'static': 'static'
            }
        }, ['region: Snowdream\n', 'host: Rozelle'])
    ]

    @patch('scripts.lambdaRun.loadEnvFile', side_effect=mockReturns)
    @patch('builtins.open', new_callable=mock_open, read_data='data')
    def test_envVar_success(self, mock_file, mock_env):
        setEnvVars('development')
        envCalls = [
            call('development', 'config/{}.yaml'),
            call('development', None)
        ]
        mock_env.assert_has_calls(envCalls)

    @patch('scripts.lambdaRun.loadEnvFile', return_value=({}, None))
    @patch('shutil.copyfile')
    def test_missing_block(self, mock_copy, mock_env):
        setEnvVars('development')
        mock_env.assert_called_once()
        mock_copy.assert_called_once_with('config.yaml', 'run_config.yaml')

    mockReturns = [
        ({
            'environment_variables': {
                'test': 'world'
            }
        }, None),
        ({
            'environment_variables': {
                'jerry': 'hello'
            }
        }, [
            'region: candyland\n',
            '# === START_ENV_VARIABLES ===\n',
            'environment_variables:\n',
            'jerry: hello\n',
            '# === END_ENV_VARIABLES ==='
            ]
        )
    ]

    @patch('scripts.lambdaRun.loadEnvFile', side_effect=mockReturns)
    def test_envVar_parsing(self, mock_env):
        m = mock_open()
        with patch('builtins.open', m, create=True):
            setEnvVars('development')
            confHandle = m()
            confHandle.write.assert_has_calls([
                call('environment_variables:\n  jerry: hello\n  test: world\n')
            ])

    @patch('scripts.lambdaRun.loadEnvFile', side_effect=mockReturns)
    @patch('builtins.open', side_effect=IOError())
    def test_envVar_permissions(self, mock_file, mock_env):
        with pytest.raises(IOError):
            setEnvVars('development')

    @patch('yaml.load', return_value={'testing': True})
    def test_load_env_success(self, mock_yaml):
        resDict, resLines = loadEnvFile('development', None)
        assert resDict['testing'] is True

    @patch('yaml.load', return_value={'testing': True})
    def test_load_env_config_success(self, mock_yaml):
        with patch('builtins.open', mock_open(), create=True):
            resDict, resLines = loadEnvFile('development', 'config/{}.yaml')
            assert resDict['testing'] is True

    @patch('yaml.load', side_effect={'testing': True})
    def test_load_env_failure(self, mock_yaml):
        with pytest.raises(FileNotFoundError):
            resDict, resLines = loadEnvFile('development', 'missing/{}.yaml')

    @patch('yaml.load', return_value=None)
    def test_load_empty_env(self, mock_yaml):
        resDict, resLines = loadEnvFile('development', None)
        assert resDict == {}

    @patch('yaml.load', side_effect=YAMLError)
    def test_read_env_failure(self, mock_yaml):
        with patch('builtins.open', mock_open(), create=True):
            with pytest.raises(YAMLError):
                resDict, resLines = loadEnvFile('development', 'config/{}.yaml')

    mockReturns = [
        ({
            'function_name': 'tester',
            'environment_variables': {
                'jerry': 'hello'
            }
        }, [
            'region: candyland\n',
            '# === START_ENV_VARIABLES ===\n',
            'environment_variables:\n',
            'jerry: hello\n',
            '# === END_ENV_VARIABLES ==='
            ]
        )
    ]

    @patch('scripts.lambdaRun.createAWSClient')
    @patch('scripts.lambdaRun.loadEnvFile', side_effect=mockReturns)
    def test_create_event_mapping(self, mock_env, mock_client):
        jsonD = ('{"EventSourceMappings": [{"EventSourceArn": "test",'
                 '"Enabled": "test", "BatchSize": "test",'
                 '"StartingPosition": "test"}]}')

        with patch('builtins.open', mock_open(read_data=jsonD), create=True):
            createEventMapping('development')

        mock_env.assert_called_once_with('development', None)
        mock_client.assert_called_once()
        mock_client().create_event_source_mapping.assert_has_calls([
            call(
                BatchSize='test',
                Enabled='test',
                EventSourceArn='test',
                FunctionName='tester',
                StartingPosition='test'
            )
        ])

    @patch('scripts.lambdaRun.createAWSClient')
    @patch('scripts.lambdaRun.loadEnvFile', side_effect=mockReturns)
    def test_at_lastest_position_event(self, mock_env, mock_client):
        jsonD = ('{"EventSourceMappings": [{"EventSourceArn": "test",'
                 '"Enabled": "test", "BatchSize": "test",'
                 '"StartingPosition": "AT_TIMESTAMP",'
                 ' "StartingPositionTimestamp": "test"}]}')
        with patch('builtins.open', mock_open(read_data=jsonD), create=True):
            createEventMapping('development')

        mock_env.assert_called_once_with('development', None)
        mock_client.assert_called_once()
        mock_client().create_event_source_mapping.assert_has_calls([
            call(
                BatchSize='test',
                Enabled='test',
                EventSourceArn='test',
                FunctionName='tester',
                StartingPosition='AT_TIMESTAMP',
                StartingPositionTimestamp='test'
            )
        ])

    def test_event_mapping_json_err(self):
        jsonD = ('{"EventSourceMappings": [{"EventSourceArn": "test",'
                 '"Enabled": "test", "BatchSize": "test",'
                 '"StartingPosition": "test"}}')

        with patch('builtins.open', mock_open(read_data=jsonD), create=True):
            with pytest.raises(json.decoder.JSONDecodeError):
                createEventMapping('development')

    @patch('builtins.open', side_effect=IOError)
    def test_event_permissions_err(self, mock_file):
        with pytest.raises(IOError):
            createEventMapping('development')

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_event_missing_err(self, mock_file):
        assert createEventMapping('development') is None

    @patch('scripts.lambdaRun.loadEnvFile')
    def test_empty_mapping_json_err(self, mock_env):
        jsonD = '{"EventSourceMappings": []}'

        with patch('builtins.open', mock_open(read_data=jsonD), create=True):
            createEventMapping('development')

        mock_env.assert_not_called()

    @patch('boto3.client', return_value=True)
    def test_create_client(self, mock_boto):
        result = createAWSClient({
            'region': 'test'
        })
        mock_boto.assert_called_once_with('lambda', region_name='test')
        assert result is True

    @patch('boto3.client', return_value=True)
    def test_create_with_access(self, mock_boto):
        result = createAWSClient({
            'region': 'test',
            'aws_access_key_id': 1,
            'aws_secret_access_key': 'secret'
        })
        mock_boto.assert_called_once_with(
            'lambda',
            region_name='test',
            aws_access_key_id=1,
            aws_secret_access_key='secret'
        )
        assert result is True
