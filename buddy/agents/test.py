from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json
import questionary
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

@dataclass
class MLTask:
    """Dataclass for storing ML development tasks"""
    task: str
    description: str
    dependencies: List[str]

@dataclass
class MLPlan:
    """Dataclass for storing the complete ML development plan"""
    model_type: str
    tasks: List[MLTask]
    evaluation_metrics: List[str]
    considerations: Dict[str, str]

class MLPlannerAgent:
    def __init__(self, model, console=None):
        """
        MLPlannerAgent: An agent that creates ML development plans based on data analysis reports.
        Takes the AnalyzerAgent's report as input and generates detailed development tasks.

        Args:
            model: The LLM model to use for planning
            console: Rich console for display
        """
        self.model = model
        self.console = console if console else Console()
        
        self.planning_prompt = """
        You are an ML Project Planning Expert. Your task is to create a detailed plan for developing 
        a machine learning model based on the provided data analysis results.

        Given the data cleaning insights and business insights from the analysis, create a structured plan that includes:
        1. Recommended model type and justification
        2. Specific coding tasks for implementation
        3. Key evaluation metrics
        4. Important considerations based on the data analysis

        Provide the plan in JSON format with the following structure:
        {
            "model_type": "Recommended model type with brief justification",
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
                "business_impact": "Considerations from business insights",
                "limitations": "Potential limitations to be aware of",
                "monitoring": "What to monitor in production"
            }
        }
        """

    def create_planning_context(self, analysis_report) -> str:
        """Creates planning context from analyzer report"""
        context = "Based on the following analysis results:\n\n"
        
        for result in analysis_report.results:
            context += f"\n{result.category.upper()} INSIGHTS:\n"
            context += f"{result.steps}\n"
            
        context += "\nCreate a detailed ML development plan that addresses the insights and challenges identified in the analysis."
        return context

    def generate_plan(self, analysis_report) -> MLPlan:
        """Generates ML development plan based on analysis report"""
        planning_context = self.create_planning_context(analysis_report)
        
        with self.console.status("[bold green]Generating ML development plan..."):
            chat_history = [
                {"role": "system", "content": self.planning_prompt},
                {"role": "user", "content": planning_context}
            ]
            
            response = self.model.query(
                chat_history,
                response_format={"type": "json_object"}
            )
            
            plan_dict = json.loads(response)
            
            # Convert dictionary to MLPlan object
            tasks = [
                MLTask(
                    task=task["task"],
                    description=task["description"],
                    dependencies=task["dependencies"]
                ) for task in plan_dict["tasks"]
            ]
            
            return MLPlan(
                model_type=plan_dict["model_type"],
                tasks=tasks,
                evaluation_metrics=plan_dict["evaluation_metrics"],
                considerations=plan_dict["considerations"]
            )

    def display_plan(self, plan: MLPlan):
        """Displays the ML development plan using rich formatting"""
        # Display model type
        self.console.print(Panel(
            f"[bold blue]ML Development Plan[/bold blue]\n\n"
            f"[bold]Recommended Model:[/bold] {plan.model_type}",
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

    def interactive_review(self, plan: MLPlan) -> MLPlan:
        """Allows interactive review and modification of the ML development plan"""
        self.display_plan(plan)
        
        while True:
            action = questionary.select(
                "Would you like to modify the plan?",
                choices=[
                    "Continue with current plan",
                    "Add task",
                    "Modify model type",
                    "Add evaluation metric",
                    "Add consideration",
                    "Exit"
                ]
            ).ask()

            if action == "Continue with current plan":
                break
            elif action == "Exit":
                sys.exit(0)
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
            elif action == "Modify model type":
                plan.model_type = questionary.text("Enter new model type and justification:").ask()
            elif action == "Add evaluation metric":
                metric = questionary.text("Enter new evaluation metric:").ask()
                plan.evaluation_metrics.append(metric)
            elif action == "Add consideration":
                category = questionary.text("Enter consideration category:").ask()
                details = questionary.text("Enter consideration details:").ask()
                plan.considerations[category] = details

            self.display_plan(plan)

        return plan

    def plan_ml_development(self, analysis_report) -> MLPlan:
        """Main method to generate and review ML development plan"""
        # Generate initial plan
        initial_plan = self.generate_plan(analysis_report)
        
        # Interactive review
        final_plan = self.interactive_review(initial_plan)
        
        return final_plan