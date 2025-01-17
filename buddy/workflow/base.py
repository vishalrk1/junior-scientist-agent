import os
import questionary
from rich.console import Console
from rich.panel import Panel

from buddy.model import load_model
from buddy.utils import print_in_box, ask_text, dataframe_validator
from buddy.agents import AdviseAgent, AnalyzerAgent, PlannerAgent
from buddy.agents.advisor import process_report

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
    """Base workflow for the data science buddy"""
    console = Console()
    model = load_model(work_dir, model)

    try:
        advisor = AdviseAgent(model, console)
        analyzer = AnalyzerAgent(model, console)
        planner = PlannerAgent(model, console)
    except Exception as e:
        console.print(f"[red]Error initializing agents: {str(e)}[/red]")
        return

    dataset = ask_text("What is the dataset you are working with?")
    if not dataset:
        print_in_box("No dataset selected. Exiting.", title="Data Buddy", color="red")
        return

    try:
        df = dataframe_validator(dataset)
    except Exception as e:
        suggested_fix = advisor.handle_missing_data(e)
        if not suggested_fix:
            print_in_box(f"Error validating dataset: {e}", title="Data Buddy", color="red")
            return
        df = dataframe_validator(suggested_fix)

    try:
        analysis_report = analyzer.analyze_data(df=df)
        dataset = advisor.exlore_dataset(dataset)
    except Exception as e:
        console.print(f"[red]Error during analysis: {str(e)}[/red]")
        return

    requirements = ask_text("What are the additional requirements for the project? (Press Enter to skip)")
    try:
        if not requirements:
            requirements = advisor.generate_default_requirements(df, analysis_report)
        
        # Extract and validate requirements
        extracted_reqs = advisor.extract_requirements(requirements)
        is_valid, issues = advisor.validate_requirements(extracted_reqs)
        
        if not is_valid:
            console.print("[yellow]Some requirements need attention:[/yellow]")
            for issue in issues:
                console.print(f"- {issue}")
            complete_reqs = advisor.gather_missing_requirements(extracted_reqs)
            requirements = advisor.format_requirements(complete_reqs)
        
        # Get project scope
        scope = advisor.get_project_scope()
        report = advisor.chat(requirements)
    except Exception as e:
        console.print(f"[red]Error processing requirements: {str(e)}[/red]")
        suggested_fix = advisor.handle_invalid_requirement(e)
        if suggested_fix:
            report = advisor.chat(suggested_fix)
        else:
            return

    print_in_box(report, title="Final Data Buddy results", color="green")

    if questionary.confirm("Do you want to generate a ML development plan?").ask():
        try:
            ml_plan = planner.generate_plan()
            if questionary.confirm("Do you want to improve the ML development plan?").ask():
                improved_plan = planner.chat(ml_plan)
                planner.save_plan(improved_plan)
            else:
                planner.save_plan(ml_plan)
        except Exception as e:
            console.print(f"[red]Error generating plan: {str(e)}[/red]")
            return
    try:
        advisor.save_report()
        console.print("[green]Project report saved successfully![/green]")
    except Exception as e:
        console.print(f"[red]Error saving report: {str(e)}[/red]")