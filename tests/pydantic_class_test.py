from pydantic import BaseModel, PositiveInt

from atro_args import Arg, InputArgs


class TestClass(BaseModel):
    name: str
    surname: str
    age: PositiveInt
    bozo: bool = False


def test_populate_pydantic_class():
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="name", arg_type=str, help="", required=False))
    input_args.add_arg(Arg(name="surname", arg_type=str, help="", required=False))
    input_args.add_arg(Arg(name="age", arg_type=int, help="", required=False))
    input_args.add_arg(Arg(name="bad_field", arg_type=int, help="", required=False))  # It will not make it as it will be filtered out.

    # Mock cli input args
    cli_input_args = ["--name", "test", "--surname", "alsotest", "--age", "10", "--bad_field", "19"]

    # Create model
    pydantic_model: TestClass = input_args.parse_args_into_pydantic_class(TestClass, cli_input_args=cli_input_args)

    # Assert
    assert pydantic_model.name == "test"
    assert pydantic_model.surname == "alsotest"
    assert pydantic_model.age == 10


def test_add_args_from_pydantic_class():
    # Setup
    input_args = InputArgs()
    input_args.add_args_from_pydantic_class(TestClass)

    args = input_args.args

    assert len(args) == 4
    assert [arg.name for arg in args] == ["name", "surname", "age", "bozo"]


def test_add_args_and_populate_using_pydantic():
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_args_from_pydantic_class(TestClass)

    # Mock cli input args
    cli_input_args = ["--name", "test", "--surname", "alsotest", "--age", "10", "--bozo", "True"]

    # Create model
    pydantic_model: TestClass = input_args.parse_args_into_pydantic_class(TestClass, cli_input_args=cli_input_args)

    # Assert
    assert pydantic_model.name == "test"
    assert pydantic_model.surname == "alsotest"
    assert pydantic_model.age == 10
    assert pydantic_model.bozo
