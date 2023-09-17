from pathlib import Path

from classes_for_test import PydanticTestClass, PydanticTestClass2, PydanticTestClassWithUnionType

from atro_args import Arg, InputArgs


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
    pydantic_model = input_args.get_cls(PydanticTestClass, cli_input_args=cli_input_args)

    # Assert
    assert pydantic_model.name == "test"
    assert pydantic_model.surname == "alsotest"
    assert pydantic_model.age == 10


def test_add_args_from_pydantic_class():
    # Setup
    input_args = InputArgs()
    input_args.add_cls(PydanticTestClass)

    args = input_args.args

    assert len(args) == 4
    assert [arg.name for arg in args] == ["name", "surname", "age", "bozo"]


def test_add_args_and_populate_using_pydantic():
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_cls(PydanticTestClass)

    # Mock cli input args
    cli_input_args = ["--name", "test", "--surname", "alsotest", "--age", "10", "--bozo", "True"]

    # Create model
    pydantic_model = input_args.get_cls(PydanticTestClass, cli_input_args=cli_input_args)

    # Assert
    assert pydantic_model.name == "test"
    assert pydantic_model.surname == "alsotest"
    assert pydantic_model.age == 10
    assert pydantic_model.bozo


def test_pydantic_populate_from_env_file():
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.set_source(Path(__file__).parent / "data_test_files" / ".env")
    resp = input_args.populate_cls(PydanticTestClass2)

    # Assert
    assert resp.random_env_file_number == 10


def test_pydantic_class_with_union_type():
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.set_source(Path(__file__).parent / "data_test_files" / ".env")
    resp = input_args.populate_cls(PydanticTestClassWithUnionType)

    # Assert
    assert resp.random_env_file_number == 10
    assert resp.app_env_file_name == Path("test")
