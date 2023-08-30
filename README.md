<!--intro-start-->

# Atro-Args

Python package that allows one to source arguments from command line arguments, environment variables, environment files and yaml files with overwritable prioritization and decent logging.

# Installation

```bash
pip install -U atro-args
```

# Basic Example

Suppose you want to obtain two variables `app_name` and `app_namespace` from cli inputs and environment variables. You can do the following:

```python
from atro_args import Arg, InputArgs
input_args = InputArgs(prefix="ATRO_TEST")
input_args.add_arg(Arg(name="app_name", arg_type=str, help="App name", required=True))
input_args.add_arg(Arg(name="app_namespace", arg_type=str, help="App name", required=True))

model = input_args.get_dict()
```

The following model will be a dictionary `dict` which will contain both `app_name` and `app_namespace` as keys with their respective values.

<!--intro-end-->

For more examples and more explanations please refer to the [documentation](https://args.atro.xyz/).
