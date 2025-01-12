import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

import os 
import questionary
import yaml
from pathlib import Path

console = Console()

@click.group()
def main():
    """Junior Data Scientist CLI"""
    pass

@main.command()
@click.option("--name", prompt="Project name", help="Project name")
def new(name):
    """Start a new project"""
    if not name:
        console.print("Please provide a project name", style="bold red")
        return
    
    platform = questionary.select(
        "Select you LLM Provider",
        choices=['OpenAI'],
    ).ask()

    api_key = None
    if platform == "OpenAI":
        api_key = questionary.text("Enter your OpenAI API key").ask()

    project_dir = os.path.join(os.getcwd(), "projects", name)
    config_dir = os.path.join(project_dir, ".databuddy")
    Path(config_dir).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(config_dir, "config.yml"), "w") as f:
        yaml.dump({
            "platform": platform, 
            "api_key": api_key
        }, f, default_flow_style=False)

    console.print(Panel.fit(
        "[bold green]Project created successfully![/]",
        title="Junior Data Scientist CLI",
        border_style="green"
    ))

if __name__ == "__main__":
    main()