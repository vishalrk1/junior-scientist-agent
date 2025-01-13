from .interaction import *
from .search import *

schema_search_arxiv = {
    'name': 'search_arxiv',
    'description': 'Search for papers on arXiv and return the top results based on keywords'
                   ' (task, model, dataset, etc.) Use this function when there is a need to search'
                   ' for research papers.',
    'parameters': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'The search query to perform'
            },
            'max_results': {
                'type': 'integer',
                'description': 'The maximum number of results to return'
            }
        }
    }
}

# Interaction related function schema
schema_ask_question = {
    'name': 'ask_question',
    'description': 'Ask a question to the user and get a response. '
                   'Use this function when there is a need to interact with the user by asking questions.',
    'parameters': {
        'type': 'object',
        'properties': {
            'question': {
                'type': 'string',
                'description': 'The question to ask the user'
            }
        }
    }
}

schema_ask_yes_no = {
    'name': 'ask_yes_no',
    'description': 'Ask a yes/no question to the user and get a response. '
                   'Use this function when there is a need to ask the user a yes/no question.',
    'parameters': {
        'type': 'object',
        'properties': {
            'question': {
                'type': 'string',
                'description': 'The yes/no question to ask the user'
            }
        }
    }
}

schema_ask_choices = {
    'name': 'ask_choices',
    'description': 'Ask a multiple-choice question to the user and get a response. '
                   'Use this function when there is a need to ask the user to choose from multiple options.',
    'parameters': {
        'type': 'object',
        'properties': {
            'question': {
                'type': 'string',
                'description': 'The multiple-choice question to ask the user'
            },
            'choices': {
                'type': 'array',
                'items': {
                    'type': 'string'
                },
                'description': 'The list of choices for the user to select from'
            }
        }
    }
}

# Data preview related function schema
schema_preview_csv_data = {
    'name': 'preview_csv_data',
    'description': 'Preview the contents of a CSV file and return the first few rows. '
                   'Use this function when there is a need to preview the data in a CSV file.',
    'parameters': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'The path of the CSV file to preview'
            },
            'limit_rows': {
                'type': 'integer',
                'description': 'The number of rows to preview, should not be a very large number. Default is 3.'
            },
            'limit_columns': {
                'type': 'integer',
                'description': 'The number of columns to preview, should not be a very large number. Default is None.'
            }
        }
    }
}

FUNCTIONS = [
    ask_question,
    ask_yes_no,
    ask_choices,
    search_arxiv
]

FUNCTION_NAMES = [func.__name__ for func in FUNCTIONS]

SEARCH_FUNCTIONS = [
    "search_arxiv",
]

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