from pathlib import Path

import pytest

from atro_args import Arg, InputArgs


@pytest.mark.parametrize("provided", [True, False])
def test_single_arg_optional(provided: bool):
    # Setup
    yaml_files = [Path(__file__).parent / "test.yaml"] if provided else []
    input_args = InputArgs(prefix="ATRO_TEST", yaml_files=yaml_files)
    input_args.add_arg(Arg(name="app_yaml_file_name", arg_type=str, help="App name", required=False))

    # Create model
    model = input_args.parse_args()

    # Assert
    assert len(model) == 1
    if provided:
        assert model.get("app_yaml_file_name") == "test"
    else:
        assert model.get("app_yaml_file_name") is None


@pytest.mark.parametrize("provided", [True, False])
def test_single_arg_required(mocker, provided: bool):
    # Setup
    yaml_files = [Path(__file__).parent / "test.yaml"] if provided else []
    input_args = InputArgs(prefix="ATRO_TEST", yaml_files=yaml_files)
    input_args.add_arg(Arg(name="random_yaml_file_number", arg_type=int, help="App name", required=True))

    # Assert
    if provided:
        model = input_args.parse_args()
        assert len(model) == 1
        assert model.get("random_yaml_file_number") == 10
        assert type(model.get("random_yaml_file_number")) == int
    else:
        with pytest.raises(Exception):
            input_args.parse_args()


def test_wrong_type():
    # Setup
    yaml_files = [Path(__file__).parent / "test.yaml"]
    input_args = InputArgs(prefix="ATRO_TEST", yaml_files=yaml_files)
    input_args.add_arg(Arg(name="app_yaml_file_name", arg_type=int, help="App name", required=True))

    # Create model
    with pytest.raises(ValueError):
        input_args.parse_args()
