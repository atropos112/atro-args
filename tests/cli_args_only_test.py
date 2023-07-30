import pytest

from atro_args import Arg, InputArgs


@pytest.mark.parametrize("provided", [True, False])
def test_single_arg_optional(provided: bool):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="app_name", arg_type=str, help="App name", required=False))

    # Mock cli input args
    cli_input_args = ["--app_name", "test"] if provided else []

    # Create model
    model = input_args.parse_args(cli_input_args=cli_input_args)

    # Assert
    assert len(model) == 1
    if provided:
        assert model.get("app_name") == "test"
    else:
        assert model.get("app_name") is None


@pytest.mark.parametrize("provided", [True, False])
def test_single_arg_required(provided: bool):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="random_number", arg_type=int, help="App name", required=True))

    # Mock cli input args
    cli_input_args = ["--random_number", "10"] if provided else []

    # Assert
    if provided:
        model = input_args.parse_args(cli_input_args=cli_input_args)
        assert len(model) == 1
        assert model.get("random_number") == 10
        assert type(model.get("random_number")) == int
    else:
        with pytest.raises(Exception):
            input_args.parse_args(cli_input_args=cli_input_args)


def test_single_arg_required_with_dash():
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="random-number", arg_type=int, help="App name", required=True))

    # Mock cli input args
    cli_input_args = ["--random-number", "10"]

    # Assert
    model = input_args.parse_args(cli_input_args=cli_input_args)
    assert len(model) == 1
    assert model.get("random-number") == 10
    assert type(model.get("random-number")) == int


def test_wrong_type():
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="random_number", arg_type=int, help="App name", required=True))

    # Mock cli input args
    cli_input_args = ["--random_number", "test"]

    # Create model
    with pytest.raises(SystemExit):
        input_args.parse_args(cli_input_args=cli_input_args)


@pytest.mark.parametrize("required_provided", [True, False])
@pytest.mark.parametrize("optional_provided", [True, False])
def test_one_required_one_optional(required_provided: bool, optional_provided: bool):
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="random_number", arg_type=int, help="App name", required=True))
    input_args.add_arg(Arg(name="app_name", arg_type=str, help="App name", required=False))

    # Mock cli input args
    cli_input_args = []
    if required_provided:
        cli_input_args.extend(["--random_number", "10"])
    if optional_provided:
        cli_input_args.extend(["--app_name", "test"])

    # Assert
    if required_provided:
        model = input_args.parse_args(cli_input_args=cli_input_args)
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
            input_args.parse_args(cli_input_args=cli_input_args)
