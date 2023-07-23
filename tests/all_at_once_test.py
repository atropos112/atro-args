from os import environ
from pathlib import Path

from atro_args import Arg, InputArgs
from atro_args.arg_type import ArgType


def test_all_inputs_at_once(mocker):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST", env_files=[Path(__file__).parent / ".env"], yaml_files=[Path(__file__).parent / "test.yaml"], arg_priority=[ArgType.cli_args, ArgType.yaml_files, ArgType.envs, ArgType.env_files])
    input_args.add_arg(Arg(name="app_name", arg_type=str, help="App name", required=True))
    input_args.add_arg(Arg(name="app_env_name", arg_type=str, help="App name", required=True))
    input_args.add_arg(Arg(name="app_env_file_name", arg_type=str, help="App name", required=True))
    input_args.add_arg(Arg(name="app_yaml_file_name", arg_type=str, help="App name", required=True))

    # Mock cli and env inputs
    cli_input_args = ["--app_name", "test_cli"]
    mocker.patch.dict(environ, {"ATRO_TEST_APP_ENV_NAME": "test_env"})

    # Create model
    model = input_args.parse_args(cli_input_args=cli_input_args)

    # Assert
    assert model.get("app_name") == "test_cli"
    assert model.get("app_env_name") == "test_env"
    assert model.get("app_env_file_name") == "test"
    assert model.get("app_yaml_file_name") == "test"


def test_priority(mocker):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST", env_files=[Path(__file__).parent / ".env"], yaml_files=[Path(__file__).parent / "test.yaml"])
    input_args.add_arg(Arg(name="app_name", arg_type=str, help="App name", required=True))

    # Mock cli and env inputs
    cli_input_args = ["--app_name", "test_cli"]
    mocker.patch.dict(environ, {"ATRO_TEST_APP_NAME": "test_env"})

    # Create model
    model = input_args.parse_args(cli_input_args=cli_input_args)

    # Assert default priority is used (cli first)
    assert model.get("app_name") == "test_cli"

    # Change priority
    arg_priority = [ArgType.envs, ArgType.cli_args, ArgType.yaml_files, ArgType.env_files]
    input_args.arg_priority = arg_priority

    # Create new model with new priority
    model = input_args.parse_args(cli_input_args=cli_input_args)

    # Assert priority change affected the result
    assert model.get("app_name") == "test_env"