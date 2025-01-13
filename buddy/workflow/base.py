import os
import questionary
from rich.console import Console
from rich.panel import Panel

from buddy.model import load_model
from buddy.utils import print_in_box, ask_text
from buddy.agents import AdviseAgent

def ask_data(data_str: str):
    """
    Ask the user to confirm the dataset.

    Args:
        data_str: the dataset string to confirm.

    Returns:
        the formatted dataset information.
    """
    if os.path.isfile(data_str) and data_str.lower().endswith(".csv"):
        return f"[green]CSV Dataset Location:[/green] {data_str}"
    else:
        return f"[green]Dataset Name:[/green] {data_str}"
    
def base(work_dir: str, model=None):
    """
    Base workflow fow the data science buddy
    """
    console = Console()
    model = load_model(work_dir, model)

    # defining the advision agent
    advisor = AdviseAgent(model, console)
    dataset = ask_text("What is the dataset you are working with?")
    if not dataset:
        print_in_box("Please provide a valid dataset.", title="Data Buddy", color="red")
        return
    dataset = advisor.exlore_dataset(dataset)

    requirements = ask_text("What are the additional requirements for the project?")
    if not requirements:
        print_in_box("Please provide the requirements.", title="Data Buddy", color="red")
        return
    report = advisor.chat(requirements)
    print_in_box(report, title="Final Data Buddy results", color="green")