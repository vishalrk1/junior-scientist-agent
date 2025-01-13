from .openai import *

from buddy.utils import get_config

MODEL_OPENAI = 'openai'

def load_model(project_dir: str, model_name: str=None):
    """
    load_model: load the model based on the configuration.
    Args:
        project_dir (str): The project directory.
        model_name (str): The model name.
    """
    config = get_config(project_dir)
    print(config)
    model = None

    if config['platform'] == MODEL_OPENAI:
        model = OpenAIModel(api_key=config['api_key'], model=model_name)
    return model