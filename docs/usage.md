# Usage

The usage of this package can be broken down to 3 steps.
1. Instantiate InputArgs class.
2. Include/Set sources where the arguments are to come from.
3. Adding arguments we want to later retreive.
4. Get the arguments in the desired form (either as an instance of a class or `dict[str, Any]`)

## Instantiate InputArg class 

The key during instatiation is to set correct `prefix` if we intend to use environment variables or environment files. For example say the `prefix` is set to "SOME_TEXT" (it will be capitalised regardless how user inputs it). Then an argument with name "someword" will be searched under environment variable "SOME_TEXT_SOMEWORD".

## Include/Set Sources

Sources are the places where the arguments are searched for. The order is important as that sets the priority, if argument is sourced from one source it will not be overwriten by next one hence the source that is checked first has the highest priority, one checked last has the lowest priority. The defaults are filled in if no source contains the data, if there are no defaults and no source has the variable it will throw if `required=True` and return `None` otherwise.

The default sources are cli-arguments,`.env` file in the PYTHONPATH and then environment variables, here cli-args have highest priority, environment variables have lowest priority.

A source can either be of type `ArgSource` such as cli-args or envs or it can be a `Path` pointing to the file that acts as a source.

Including will append source/s to the end of the list while using set completely resets the sources, not the list is pre-filled with the 3 defaults mentioned above to begin with.

# Add arguments


# Get arguments

