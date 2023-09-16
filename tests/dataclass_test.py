from classes_for_test import DataTestClass

from atro_args import Arg, InputArgs


def test_populate_dataclass():
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="name", arg_type=str, help="", required=False))
    input_args.add_arg(Arg(name="surname", arg_type=str, help="", required=False))
    input_args.add_arg(Arg(name="age", arg_type=int, help="", required=False))
    input_args.add_arg(Arg(name="bad_field", arg_type=int, help="", required=False))  # It will not make it as it will be filtered out.

    # Mock cli input args
    cli_input_args = ["--name", "test", "--surname", "alsotest", "--age", "10", "--bad_field", "19"]

    # Create model
    model = input_args.get_cls(DataTestClass, cli_input_args=cli_input_args)

    # Assert
    assert model.name == "test"
    assert model.surname == "alsotest"
    assert model.age == 10


def test_add_args_from_dataclass():
    # Setup
    import sys

    sys.argv
    input_args = InputArgs()
    input_args.add_cls(DataTestClass)

    args = input_args.args

    assert len(args) == 4
    assert [arg.name for arg in args] == ["name", "surname", "age", "bozo"]


def test_add_args_and_populate_using_dataclass():
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_cls(DataTestClass)

    # Mock cli input args
    cli_input_args = ["--name", "test", "--surname", "alsotest", "--age", "10", "--bozo", "True"]

    # Create model
    data_model = input_args.get_cls(DataTestClass, cli_input_args=cli_input_args)

    # Assert
    assert data_model.name == "test"
    assert data_model.surname == "alsotest"
    assert data_model.age == 10
    assert data_model.bozo
