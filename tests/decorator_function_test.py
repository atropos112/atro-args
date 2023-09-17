import json
from pathlib import Path

import pytest

from atro_args import get_arg, include_source, input_args


def test_decorators_with_json_source():
    json_file_path = Path(__file__).parent / "data_test_files" / "test.json"

    @input_args()
    @include_source(json_file_path)
    def sample_function(test_number: int = get_arg(), test_text: str = get_arg()):
        return test_text, test_number

    # Execute the function
    result_text, result_number = sample_function()

    # Load the source JSON file
    with open(json_file_path) as arg_file:
        data = json.load(arg_file)

    # Assert the function's output matches the values in JSON
    assert result_text == data["test_text"]
    assert result_number == data["test_number"]


def test_decorators_with_missing_json_source():
    # Test behavior when the JSON source file does not exist
    json_file_path = Path(__file__).parent / "non_existent.json"

    @input_args()
    @include_source(json_file_path)
    def sample_function(test_number: int = get_arg()):
        return test_number

    # When executing the function with a non-existent source, expect a FileNotFoundError
    with pytest.raises(FileNotFoundError):
        sample_function()


def test_decorators_with_improper_json_keys():
    # Test behavior when JSON does not contain all the necessary keys
    json_file_path = Path(__file__).parent / "data_test_files" / "test.json"

    @input_args()
    @include_source(json_file_path)
    def sample_function(test_number: int = get_arg(), missing_argument: str = get_arg()):
        return missing_argument, test_number

    # When executing the function, expect a KeyError due to the missing JSON key
    with pytest.raises(KeyError, match="\"Missing required arguments: 'missing_argument'\""):
        sample_function()


def test_decorators_with_incorrect_value_type():
    # Test behavior when the JSON values do not match the defined argument types
    json_file_path = Path(__file__).parent / "data_test_files" / "test.json"

    @input_args()
    @include_source(json_file_path)
    def sample_function(test_text: int = get_arg()):
        return test_text

    # When executing the function, expect a TypeError due to the incorrect type in JSON values
    with pytest.raises(TypeError, match="Could not load Hello as <class 'int'>."):
        sample_function()
