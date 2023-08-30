from atro_args import Arg, InputArgs


def test_list_via_cli():
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="some_list", arg_type=list, help="", required=True))
    input_args.add_arg(Arg(name="some_list1", arg_type=list, help="", required=True))
    input_args.add_arg(Arg(name="some_list2", arg_type=list, help="", required=True))

    # Mock cli input args
    cli_input_args: list[str] = ["--some_list", "['blah', 'blah2']", "--some_list1", '["blah", "blah2"]', "--some_list2", "[]"]

    # Create model
    model = input_args.get_dict(cli_input_args=cli_input_args)

    # Assert
    assert len(model) == 3

    assert type(model.get("some_list")) == list
    assert type(model.get("some_list1")) == list
    assert type(model.get("some_list2")) == list

    assert model.get("some_list") == ["blah", "blah2"]
    assert model.get("some_list1") == ["blah", "blah2"]
    assert model.get("some_list2") == []


def test_dict_via_cli():
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="some_dict", arg_type=dict, help="", required=True))
    input_args.add_arg(Arg(name="some_dict1", arg_type=dict, help="", required=True))
    input_args.add_arg(Arg(name="some_dict2", arg_type=dict, help="", required=True))

    # Mock cli input args
    cli_input_args: list[str] = ["--some_dict", "{'blah': 'blah2'}", "--some_dict1", '{"blah": "blah2"}', "--some_dict2", "{ }"]

    # Create model
    model = input_args.get_dict(cli_input_args=cli_input_args)

    # Assert
    assert len(model) == 3

    assert type(model.get("some_dict")) == dict
    assert type(model.get("some_dict1")) == dict
    assert type(model.get("some_dict2")) == dict

    assert model.get("some_dict") == {"blah": "blah2"}
    assert model.get("some_dict1") == {"blah": "blah2"}
    assert model.get("some_dict2") == {}


def test_basic_via_cli():
    # Setup
    input_args = InputArgs(prefix="ATRO_TEST")
    input_args.add_arg(Arg(name="some_basic", arg_type=float, help="", required=True))
    input_args.add_arg(Arg(name="some_basic1", arg_type=int, help="", required=True))
    input_args.add_arg(Arg(name="some_basic2", arg_type=bool, help="", required=True))
    input_args.add_arg(Arg(name="some_basic3", arg_type=str, help="", required=True))

    # Mock cli input args
    cli_input_args: list[str] = ["--some_basic", "1", "--some_basic1", "  2  ", "--some_basic2", " true ", "--some_basic3", "hello"]

    # Create model
    model = input_args.get_dict(cli_input_args=cli_input_args)

    # Assert
    assert len(model) == 4

    assert type(model.get("some_basic")) == float
    assert type(model.get("some_basic1")) == int
    assert type(model.get("some_basic2")) == bool
    assert type(model.get("some_basic3")) == str

    assert model.get("some_basic") == 1.0
    assert model.get("some_basic1") == 2
    assert model.get("some_basic2")
    assert model.get("some_basic3") == "hello"
