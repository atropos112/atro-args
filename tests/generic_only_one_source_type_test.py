from os import environ
from pathlib import Path

import pytest

from atro_args import Arg, InputArgs
from atro_args.entities.arg_source import ArgSource

# list of different file formats for testing
test_data_formats: list[str] = ["ini", "yaml", "json", "toml", "env_file", ArgSource.cli, ArgSource.envs]


@pytest.mark.parametrize("source_format", test_data_formats)
@pytest.mark.parametrize("provided", [True, False])
def test_single_arg_optional(mocker, provided: bool, source_format: str):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    if provided:
        input_args.set_source(generic_test_file_path(source_format))

    input_args.add_arg(Arg(name="app_name", arg_type=str, help="My App", required=False))

    # Create model
    model = input_args.get_dict(cli_input_args=mock_if_argsource(source_format, mocker, provided))

    # Assert
    assert len(model) == 1
    if provided:
        assert model.get("app_name") == "My App"
    else:
        assert model.get("app_name") is None


@pytest.mark.parametrize("source_format", test_data_formats)
@pytest.mark.parametrize("provided", [True, False])
def test_single_arg_required(mocker, provided: bool, source_format: str):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    if provided:
        input_args.set_source(generic_test_file_path(source_format))

    input_args.add_arg(Arg(name="app_number", arg_type=int, help="My App", required=True))

    # Assert
    if provided:
        model = input_args.get_dict(cli_input_args=mock_if_argsource(source_format, mocker, provided))
        assert len(model) == 1
        assert model.get("app_number") == 10
        assert type(model.get("app_number")) == int
    else:
        with pytest.raises(Exception):
            input_args.get_dict()


@pytest.mark.parametrize("source_format", test_data_formats)
def test_wrong_type(mocker, source_format: str):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.set_source(generic_test_file_path(source_format))

    input_args.add_arg(Arg(name="app_name", arg_type=int, help="My App", required=True))

    # Create model
    with pytest.raises(TypeError):
        input_args.get_dict(cli_input_args=mock_if_argsource(source_format, mocker))


# region helpers
def generic_test_file_path(source_format: str) -> Path | ArgSource:
    if source_format == ArgSource.envs:
        return ArgSource.envs
    elif source_format == ArgSource.cli:
        return ArgSource.cli
    elif source_format == "env_file":
        source_format = "env"

    return Path(__file__).parent / "data_test_files" / "generic" / f"test.{source_format}"


def mock_if_argsource(source_format: str, mocker, provided: bool = True) -> list[str] | None:
    # Have to mock if cli or envs format
    cli_input_args = ["--app_name", "My App", "--app_number", "10"] if provided and source_format == ArgSource.cli else None
    if provided and source_format == ArgSource.envs:
        mocker.patch.dict(environ, {"ATRO_TEST_APP_NAME": "My App", "ATRO_TEST_APP_NUMBER": "10"})

    return cli_input_args


# endregion
