from .interaction import *

FUNCTIONS = [
    ask_question,
    ask_yes_no,
    ask_choices,
]

FUNCTION_NAMES = [func.__name__ for func in FUNCTIONS]

# Function related utility functions
def get_function(function_name: str):
    """
    Get the function schema by the given function name.
    :param function_name: the function name.
    :return: the function schema.
    """
    for func in FUNCTIONS:
        if func.__name__ == function_name:
            return func

    raise ValueError(f"Function {function_name} is not supported.")


def process_function_name(function_name: str):
    """
    Process the function name to avoid the LLM handling errors.
    :param function_name: the generated function name.
    :return: the correct function name.
    """
    for func in FUNCTION_NAMES:
        if func in function_name:
            return func

    raise ValueError(f"Function {function_name} is not supported.")