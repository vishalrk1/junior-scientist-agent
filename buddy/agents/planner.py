import sys
import pickle
import json
import questionary

from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import List, Dict, Any, Optional
from pathlib import Path

from buddy.utils import get_config
from buddy.dataclass import AnalysisReport, MLTask, MLPlan, AdvisorReport
from .base import BaseAgent

class PlannerAgent(BaseAgent):
    def __init__(self, model, console: Optional[Console] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(model, console, config)
        self.sys_prompt = self._prepare_prompt("""
        You are an ML project planning expert who creates detailed development plans.
        Break down complex ML projects into manageable steps and milestones.
        """)
        self.report_dir = Path("analysis_reports")
        self.report_dir.mkdir(exist_ok=True)

        self.analysis_report: AnalysisReport = self._load_analysis_report()
        self.advisor_report: Optional[AdvisorReport] = self._load_advisor_report()

        self.json_mode_prompt = """
        Provide the plan in JSON format with the following structure:
        {
            "model": "Recommended models with brief justification",
            "tasks": [
                {
                    "task": "Task name",
                    "description": "Detailed description with specific implementation instructions",
                    "dependencies": ["dependent_task_names"]
                }
            ],
            "evaluation_metrics": ["list of recommended metrics"],
            "considerations": {
                "data_quality": "Considerations from data cleaning analysis",
                "limitations": "Potential limitations to be aware of",
            }
        }
        """
    
    def _load_analysis_report(self) -> AnalysisReport:
        config = get_config()
        if not config:
            self.console.print(Panel("No analysis report found. Please run the analysis agent first.", title="Planner Agent"))
            sys.exit(0)
        dataset_hash = config.get("dataset_hash")
        report_path = self.report_dir / f"{dataset_hash}.pkl"
        if report_path.exists():
            try:
                with open(report_path, "rb") as file:
                    return pickle.load(file)
            except Exception as e:
                self.console.print(f"[red]Error loading report: {str(e)}")
                return None
    
    def _load_advisor_report(self) -> Optional[AdvisorReport]:
        config = get_config()
        if not config:
            self.console.print(Panel("No analysis report found. Please run the analysis agent first.", title="Planner Agent"))
            sys.exit(0)
        dataset_hash = config.get("dataset_hash")
        report_path = self.report_dir / f"advisory_{dataset_hash}.json"
        if report_path.exists():
            try:
                with open(report_path, "r", encoding="utf-8") as file:
                    return AdvisorReport(**json.load(file))
            except Exception as e:
                self.console.print(f"[red]Error loading advisor report: {str(e)}")
                return None
        self.console.print("[yellow]Warning: No advisor report found.")
        return None
            
    def _create_system_prompt(self, model_or_algorithm=None) -> str:
        if not self.advisor_report:
            return """You are an ML Project Planning Expert. Please provide your response in JSON format."""

        return f"""
        You are an ML Project Planning Expert. Your task is to create a detailed plan for developing 
        a machine learning model based on the provided data analysis results. Please provide your response in JSON format.

        ## Core Principles
        1. DEPTH OF REASONING 
        - Engage in extensive contemplation (minimum 10,000 characters) 
        - Express thoughts in natural, conversational internal monologue Break down complex thoughts into simple, atomic steps 
        - Embrace uncertainty and revision of previous thoughts 
        2. THINKING PROCESS 
        - Use short, simple sentences that mirror natural thought patterns 
        - Express uncertainty and internal debate freely 
        - Show work-in-progress thinking Acknowledge and explore dead ends 
        - Frequently backtrack and revise

        Given the data cleaning insights and business insights from the analysis, create a structured plan that includes:
        1. Choose the best performing model from ${model_or_algorithm if model_or_algorithm else self.advisor_report.model_or_algorithm} based on the analysis.
        2. Specific & break down coding tasks for implementation and training the model on ${self.advisor_report.frameworks} using ${self.advisor_report.training_method}.
        3. Explain the key evaluation metrics like ${self.advisor_report.evaluation_metric} and the device to be used for training.
        4. use the data summary to create a detailed plan that includes the limitations.
        5. break down the process inro small steps with detailed description and dependencies.
        """ + """
        Please respond with a valid JSON object using the following structure:
        {
            "model": "Recommended models with brief justification",
            "tasks": [
                {
                    "task": "Task name",
                    "description": "Detailed description with specific implementation instructions",
                    "dependencies": ["dependent_task_names"]
                }
            ],
            "evaluation_metrics": ["list of recommended metrics"],
            "considerations": {
                "data_quality": "Considerations from data cleaning analysis",
                "limitations": "Potential limitations to be aware of"
            }
        }
        """
            
    def create_planning_context(self, analysis_report: AnalysisReport) -> str:
        """Creates planning context from analyzer report"""
        context = "Please provide the development plan in JSON format based on the following analysis results:\n\n"
        
        for result in analysis_report.results:
            context += f"\n{result.category.upper()} INSIGHTS:\n"
            context += f"{result.steps}\n"
            
        context += "\nCreate a detailed ML development plan that addresses the insights and challenges identified in the analysis."
        return context
    
    def display_plan(self, plan: MLPlan):
        """Displays the ML development plan using rich formatting"""
        # Display model type
        self.console.print(Panel(
            f"[bold blue]ML Development Plan[/bold blue]\n\n"
            f"[bold]Recommended Model:[/bold] {plan.model}",
            title="Plan Overview"
        ))

        # Display tasks
        tasks_table = Table(title="Development Tasks")
        tasks_table.add_column("Task", style="cyan")
        tasks_table.add_column("Description", style="white")
        tasks_table.add_column("Dependencies", style="yellow")

        for task in plan.tasks:
            tasks_table.add_row(
                task.task,
                task.description,
                ", ".join(task.dependencies)
            )

        self.console.print(tasks_table)

        # Display evaluation metrics
        metrics_panel = Panel(
            "\n".join(f"• {metric}" for metric in plan.evaluation_metrics),
            title="[bold]Evaluation Metrics[/bold]",
            border_style="green"
        )
        self.console.print(metrics_panel)

        # Display considerations
        considerations_table = Table(title="Important Considerations")
        considerations_table.add_column("Category", style="cyan")
        considerations_table.add_column("Details", style="white")

        for category, details in plan.considerations.items():
            considerations_table.add_row(
                category.replace("_", " ").title(),
                details
            )

        self.console.print(considerations_table)

    def generate_plan(self, model_or_algorithm=None) -> MLPlan:
        with self.console.status("[bold green]Generating ML development plan...") as status:
            chat_history = [
                {"role": "system", "content": self.sys_prompt},
                {"role": "user", "content": self.create_planning_context(self.analysis_report)}
            ]
            
            res = self.model.query(
                chat_history,
                response_format={"type": "json_object"}
            )

            plan_dict = json.loads(res)
            tasks = [
                MLTask(
                    task=task["task"],
                    description=task["description"],
                    dependencies=task["dependencies"]
                ) for task in plan_dict["tasks"]
            ]

            plan = MLPlan(
                model=plan_dict["model"],
                tasks=tasks,
                evaluation_metrics=plan_dict["evaluation_metrics"],
                considerations=plan_dict["considerations"]
            )

            self.display_plan(plan)
            return plan
    
    def chat(self, plan: MLPlan) -> MLPlan:
        while True:
            action = questionary.select(
                "\nWould you like to modify the plan?",
                choices=[
                    "Continue with current plan",
                    "Add task",
                    "Modify model",
                    "Add consideration",
                    "Exit"
                ]
            ).ask()

            if action == "Continue with current plan" or action == "Exit":
                break
            elif action == "Add task":
                task_name = questionary.text("Enter task name:").ask()
                description = questionary.text("Enter task description:").ask()
                dependencies = questionary.text("Enter dependencies (comma-separated):").ask()
                
                new_task = MLTask(
                    task=task_name,
                    description=description,
                    dependencies=dependencies.split(",") if dependencies else []
                )
                plan.tasks.append(new_task)
            elif action == "Modify model":
                model = questionary.text("Enter new model that you want to use").ask()
                self.generate_plan(model_or_algorithm=model)
            elif action == "Add consideration":
                category = questionary.text("Enter consideration category:").ask()
                details = questionary.text("Enter consideration details:").ask()
                plan.considerations[category] = details
        
        return plan

    def save_plan(self, plan: MLPlan):
        """
        Saves the final ML development plan to the 'ml_plans' directory as a JSON file.
        """
        plan_dir = Path("ml_plans")
        plan_dir.mkdir(exist_ok=True)
        dataset_hash = getattr(self.analysis_report, "dataset_hash", "unknown_dataset")
        plan_file = plan_dir / f"ml_plan_{dataset_hash}.json"

        with open(plan_file, "w", encoding="utf-8") as f:
            json.dump({
                "model": plan.model,
                "tasks": [t.__dict__ for t in plan.tasks],
                "evaluation_metrics": plan.evaluation_metrics,
                "considerations": plan.considerations
            }, f, indent=4)
        
        self.console.print(f"[green]ML plan saved to {plan_file}[/green]")
