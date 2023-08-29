from os import environ
from pathlib import Path
import dataclasses

from atro_args import Arg, InputArgs
from atro_args.arg_source import ArgSource


def test_all_inputs_at_once(mocker):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST", env_files=[Path(__file__).parent / ".env"], yaml_files=[Path(__file__).parent / "test.yaml"], arg_priority=[ArgSource.cli_args, ArgSource.yaml_files, ArgSource.envs, ArgSource.env_files])
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


@dataclasses.dataclass
class TestDataClass:
    name: str
    age: int

def test_add_dataclass(mocker):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST", env_files=[Path(__file__).parent / ".env"], yaml_files=[Path(__file__).parent / "test.yaml"])
    input_args.add_dataclass(TestDataClass)

    # Mock cli and env inputs
    cli_input_args = ["--name", "test_cli", "--age", "30"]
    mocker.patch.dict(environ, {"ATRO_TEST_NAME": "test_env", "ATRO_TEST_AGE": "30"})

    # Create model
    model = input_args.parse_args(cli_input_args=cli_input_args)

    # Assert
    assert model.get("name") == "test_cli"
    assert isinstance(model.get("name"), str)
    assert model.get("age") == 30
    assert isinstance(model.get("age"), int)
