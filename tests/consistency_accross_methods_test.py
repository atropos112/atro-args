from inspect import signature

from atro_args import InputArgs
from atro_args.entities.arg_signature import AtroArgSignature


def test_parameter_types_and_model_field_types_alignment():
    # get the names and types of the add method parameters
    add_parameters = signature(InputArgs.add).parameters

    # map each parameter's name to its annotated type
    add_param_type_mapping = {param_name: param.annotation for param_name, param in add_parameters.items()}

    # get the model field names and their types
    model_fields = AtroArgSignature.__annotations__

    # Verify the type matching
    for model_field_name, model_field_type in model_fields.items():
        if model_field_name == "name" or model_field_name == "arg_type":
            # name and arg_type are optional as we can infer them from the signature of the function that is being decorated.
            assert model_field_type == add_param_type_mapping.get(model_field_name, None) | None
        else:
            assert add_param_type_mapping.get(model_field_name, None) == model_field_type
