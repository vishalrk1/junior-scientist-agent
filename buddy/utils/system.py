import os
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from typing import Any, Dict, Optional

def print_in_box(text: str, console: Optional[Console] = None, title: str = "", color: str = "white") -> None:
    """
    Print the text in a box.
    :param text: the text to print.
    :param console: the console to print the text.
    :param title: the title of the box.
    :param color: the border color.
    :return:
    """
    console = console or Console()

    panel = Panel(text, title=title, border_style=color, expand=True)
    console.print(panel)


def ask_text(question: str, title: str = "User", console: Optional[Console] = None) -> str:
    """
    Display a question in a panel and prompt the user for an answer.
    :param question: the question to display.
    :param title: the title of the panel.
    :param console: the console to use.
    :return: the user's answer.
    """
    console = console or Console()

    console.print(Panel(question, title="Data buddy", border_style="purple"))
    answer = Prompt.ask(f"Type your answer here")
    console.print(Panel(answer, title=title))
    return answer

def get_config(workdir: str = None) -> Optional[Dict[str, Any]]:
    """
    Get the configuration file.
    :workdir: the project directory.
    :return: the configuration file.
    """
    config_dir = os.path.join(workdir or os.getcwd(), ".databuddy")
    config_path = os.path.join(config_dir, 'config.yml')
    if not os.path.exists(config_path):
        return None
    with  open(config_path, 'r') as f:
        return yaml.safe_load(f)
    
def update_config(dataDict,  workdir=None) -> Optional[Dict[str, Any]]:
    """
    Update the configuration file with new fields.
    :workdir: the project directory.
    dataDict: the dictionary containing new fields to add.
    :return: the updated configuration file.
    """
    config_dir = os.path.join(workdir or os.getcwd(), ".databuddy")
    config_path = os.path.join(config_dir, 'config.yml')
        
    if not os.path.exists(config_path):
        return None
        
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f) or {}
        
    config.update(dataDict)
        
    with open(config_path, 'w') as f:
        yaml.safe_dump(config, f)
        
    return config