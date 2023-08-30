from pathlib import Path

import pytest

from atro_args import Arg, InputArgs


@pytest.mark.parametrize("provided", [True, False])
def test_single_arg_optional(provided: bool):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    if provided:
        input_args.include(Path(__file__).parent / ".env")
    input_args.add_arg(Arg(name="app_env_file_name", arg_type=str, help="App name", required=False))

    # Create model
    model = input_args.get_dict()

    # Assert
    assert len(model) == 1
    if provided:
        assert model.get("app_env_file_name") == "test"
    else:
        assert model.get("app_env_file_name") is None


@pytest.mark.parametrize("provided", [True, False])
def test_single_arg_required(mocker, provided: bool):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    if provided:
        input_args.include(Path(__file__).parent / ".env")
    input_args.add_arg(Arg(name="random_env_file_number", arg_type=int, help="App name", required=True))

    # Assert
    if provided:
        model = input_args.get_dict()
        assert len(model) == 1
        assert model.get("random_env_file_number") == 10
        assert type(model.get("random_env_file_number")) == int
    else:
        with pytest.raises(Exception):
            input_args.get_dict()


def test_wrong_type():
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.include(Path(__file__).parent / ".env")
    input_args.add_arg(Arg(name="app_env_file_name", arg_type=int, help="App name", required=True))

    # Create model
    with pytest.raises(ValueError):
        input_args.get_dict()
