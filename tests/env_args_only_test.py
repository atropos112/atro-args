from os import environ

import pytest

from atro_args import Arg, InputArgs


@pytest.mark.parametrize("provided", [True, False])
def test_single_arg_optional(mocker, provided: bool):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="app_name", arg_type=str, help="App name", required=False))

    # Mock envs
    if provided:
        mocker.patch.dict(environ, {"ATRO_TEST_APP_NAME": "test"})

    # Create model
    model = input_args.parse_args()

    # Assert
    assert len(model) == 1
    if provided:
        assert model.get("app_name") == "test"
    else:
        assert model.get("app_name") is None


@pytest.mark.parametrize("provided", [True, False])
def test_single_arg_required(mocker, provided: bool):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="random_number", arg_type=int, help="App name", required=True))

    # Mock envs
    if provided:
        mocker.patch.dict(environ, {"ATRO_TEST_RANDOM_NUMBER": "10"})

    # Assert
    if provided:
        model = input_args.parse_args()
        assert len(model) == 1
        assert model.get("random_number") == 10
        assert type(model.get("random_number")) == int
    else:
        with pytest.raises(Exception):
            input_args.parse_args()


def test_wrong_type(mocker):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="random_number", arg_type=int, help="App name", required=True))

    # Mock envs
    mocker.patch.dict(environ, {"ATRO_TEST_RANDOM_NUMBER": "test"})

    # Create model
    with pytest.raises(TypeError):
        input_args.parse_args()


@pytest.mark.parametrize("required_provided", [True, False])
@pytest.mark.parametrize("optional_provided", [True, False])
def test_one_required_one_optional(mocker, required_provided: bool, optional_provided: bool):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="random_number", arg_type=int, help="App name", required=True))
    input_args.add_arg(Arg(name="app_name", arg_type=str, help="App name", required=False))

    # Mock cli input args
    if required_provided:
        mocker.patch.dict(environ, {"ATRO_TEST_RANDOM_NUMBER": "10"})
    if optional_provided:
        mocker.patch.dict(environ, {"ATRO_TEST_APP_NAME": "test"})

    # Assert
    if required_provided:
        model = input_args.parse_args()
        assert len(model) == 2
        if optional_provided:
            assert model.get("app_name") == "test"
            assert type(model.get("app_name")) == str
        else:
            assert model.get("app_name") is None
        assert model.get("random_number") == 10
        assert type(model.get("random_number")) == int
    else:
        with pytest.raises(Exception):
            input_args.parse_args()
