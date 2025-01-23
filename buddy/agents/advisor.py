import sys
import json
import textwrap
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from buddy.function import * 
from buddy.utils import print_in_box, clean_json_string, update_config, get_config
from buddy.dataclass import AdvisorReport
from .base import BaseAgent
from typing import Optional, Dict, Any

def process_report(requirement: str, suggestions: dict):
    return textwrap.dedent(f"""
    [green]Suggestion Summary:[/green] {suggestions.get('suggestion')}

    [green]Task:[/green] {suggestions.get('task')}
    [green]Model:[/green] {suggestions.get('model_or_algorithm')}
    [green]Training Strategy:[/green] {suggestions.get('training_method')}
    [green]Evaluation Metric:[/green] {suggestions.get('evaluation_metric')}
    [green]Training Device:[/green] {suggestions.get('device')}

    [green]Reference:[/green] {suggestions.get('reference')}
    [green]Dependency:[/green] {suggestions.get('frameworks')}
    """).strip()

class AdviseAgent(BaseAgent):
    def __init__(self, model, console: Optional[Console] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(model, console, config)
        self.sys_prompt = self._prepare_prompt("""
        You are an ML expert advisor who helps data scientists choose the right approach.
        Provide detailed recommendations based on data analysis and requirements.
        """)

    def handle_missing_data(self, error):
        """Handle cases where data is missing"""
        self.console.print("[yellow]Warning: Missing data detected[/yellow]")
        alternatives = self.suggest_data_alternatives()
        return self.process_alternatives(alternatives)

    def handle_invalid_requirement(self, error):
        """Handle invalid requirements"""
        self.console.print("[yellow]Warning: Invalid requirement detected[/yellow]")
        return self.suggest_requirement_fix(error)

    def handle_model_error(self, error):
        """Handle model-related errors"""
        self.console.print("[red]Error: Model failed to process request[/red]")
        return self.suggest_model_alternatives()

    def validate_requirements(self, requirements: dict) -> tuple[bool, list]:
        """Validate requirements and return status and issues"""
        issues = []
        is_valid = True
        
        required_fields = ['task_type', 'performance_metric']
        for field in required_fields:
            if not requirements.get(field):
                issues.append(f"Missing {field}")
                is_valid = False
        
        return is_valid, issues

    def enhance_requirements(self, requirements: dict) -> dict:
        """Enhance requirements with AI-suggested improvements"""
        enhancement_prompt = f"""
        Given these requirements: {json.dumps(requirements)}
        Suggest improvements or additions that could lead to better ML solutions.
        Focus on practical enhancements that add value.
        """
        
        chat_history = [{"role": "user", "content": enhancement_prompt}]
        suggestions = json.loads(self.model.query(chat_history, response_format={"type": "json_object"}))
        
        return self.merge_requirements(requirements, suggestions)

    def merge_requirements(self, original: dict, suggestions: dict) -> dict:
        """Merge original requirements with suggestions"""
        merged = original.copy()
        for key, value in suggestions.items():
            if not merged.get(key) and value:
                if questionary.confirm(f"Add suggested {key}: {value}?").ask():
                    merged[key] = value
        return merged

    def exlore_dataset(self, dataset: str):
        """
        Explore the dataset and give a summary of the dataset.

        Args:
            dataset: the user's input dataset to explore.
        """
        system_prompt = """
        You are an Machine learning Product Manager, you are going to collaborate with the user to plan
        the ML project, in the use of the dataset. Your approach mirrors human stream-of- consciousness thinking,
        """
        chat_history = [{"role": "system", "content": system_prompt}]

        # verify whether the user's dataset is unclear or blur
        user_prompt = f"""
        The dataset provided by the user is: `{dataset}`

        Your task is to determine if the dataset refers to:
        1. A specific dataset name, or
        2. A file path.

        Response format: Yes / No
        - Yes: if the dataset is clearly identifiable as either a specific dataset name or a file path.
        - No: if the dataset cannot be clearly identified as either a specific dataset name or a file path.
        """
        with self.console.status("Exploring the dataset..."):
            chat_history.append({"role": "user", "content": user_prompt})
            text = self.model.query(chat_history)
            chat_history.append({"role": "assistant", "content": text})
            if "yes" in text.lower():
                return dataset

        # recommend some datasets based on the users' description
        user_prompt = f"""
        Since the user has not provided a specific dataset, suggest up to five publicly available datasets
        that best match the user's description ({dataset}). Ensure your recommendations are concise and
        include a clear explanation (within 100 words) for why each dataset is appropriate.

        Json output format:
        {{
            "datasets": ["xxx", "xxx", "xxx"],
            "reason": "Based on the user's dataset description..."
        }}
        """
        with self.console.status("Data Buddy is suggesting datasets..."):
            chat_history.append({"role": "user", "content": user_prompt})
            text = self.model.query(
                chat_history,
                response_format={"type": "json_object"}
            )
            chat_history.append({"role": "assistant", "content": text})
            suggestions = json.loads(text)

        print_in_box("Which datasets would you like?", title="Data Buddy", color="green")
        return questionary.select("Type your answer here:", choices=suggestions['datasets']).ask()

    def _get_report_path(self, dataset_hash: str) -> Path:
        """Get path for report file"""
        return self.report_dir / f"advisory_{dataset_hash}.json"
    
    def save_report(self):
        """
        Save the report to the chat history.

        Args:
            report: the report to save.
        """
        config = get_config()
        if not config:
            self.console.print(Panel("No analysis report found. Please run the analysis agent first.", title="Planner Agent"))
            sys.exit(0)
        dataset_hash = config.get("dataset_hash")
        report_path = self._get_report_path(dataset_hash)

        with open(report_path, "w") as file:
            json.dump(self.json_report, file, indent=4)

    def extract_requirements(self, text: str) -> dict:
        """Extract structured requirements from free text"""
        prompt = """
        Extract requirements from the following text. If a requirement is not mentioned, 
        mark it as None. Format as JSON:
        {
            "task_type": "identified task or None",
            "performance_metric": "identified metrics or None",
            "constraints": "identified constraints or None",
            "business_goal": "identified goal or None"
        }
        Text: """ + text

        chat_history = [{"role": "user", "content": prompt}]
        response = self.model.query(chat_history, response_format={"type": "json_object"})
        return json.loads(response)

    def gather_missing_requirements(self, requirements: dict) -> dict:
        """Interactively gather missing requirements"""
        complete_requirements = requirements.copy()
        
        for key, value in complete_requirements.items():
            if not value:
                if questionary.confirm(f"Would you like to specify {key}?").ask():
                    complete_requirements[key] = questionary.text(self.requirement_prompts[key]).ask()
                else:
                    # Auto-suggest based on dataset and context
                    suggestion = self.suggest_requirement(key)
                    if questionary.confirm(f"I suggest '{suggestion}' for {key}. Accept?").ask():
                        complete_requirements[key] = suggestion

        return complete_requirements

    def suggest_requirement(self, requirement_type: str) -> str:
        """Suggest requirements based on dataset characteristics and context"""
        prompt = f"""Based on the dataset and context, suggest a suitable {requirement_type}.
        Consider: dataset characteristics, common industry practices, and best practices."""
        
        chat_history = [{"role": "user", "content": prompt}]
        return self.model.query(chat_history)

    def get_project_scope(self) -> dict:
        """Analyze and suggest project scope"""
        scope_questions = [
            "What is the project timeline?",
            "What technical resources are available?"
        ]
        
        scope = {}
        for question in scope_questions:
            if questionary.confirm(f"Would you like to specify {question}?").ask():
                scope[question] = questionary.text(question).ask()
            else:
                scope[question] = "Not specified"
        
        return scope

    def suggest(self, requirements: str):
        """
        Suggest the machine learning task/model/algorithm to use based on the user's requirements.

        Args:
            requirements: the user's requirements.
        """
        scope = self.get_project_scope()
        
        # Add scope to requirements
        enhanced_requirements = f"""
        Requirements: {requirements}
        Project Scope: {json.dumps(scope, indent=2)}
        """
        
        self.chat_history.append({"role": "user", "content": enhanced_requirements})
        with self.console.status("Suggesting the best ML task/model/algorithm..."):
            text = self.model.query(
                self.chat_history,
                function_call='auto',
                functions=self.function,
                response_format={"type": "json_object"}
            )
            self.chat_history.append({"role": "assistant", "content": text})

            try:
                suggestions = json.loads(text)
            except json.JSONDecodeError as e:
                suggestions = clean_json_string(text)
            
            # Store the suggestions in json_report
            self.json_report = suggestions
            return process_report(requirements, suggestions)
    
    def chat(self, requirements: str = None):
        """
        Users can chat with the advisor.
        Args:
            requirements: the user's requirements.
        """
        if not requirements:
            requirements = "Please analyze the dataset and suggest an appropriate ML approach."

        extracted_reqs = self.extract_requirements(requirements)
        complete_reqs = self.gather_missing_requirements(extracted_reqs)
        
        # Format complete requirements into a detailed prompt
        detailed_prompt = self.format_requirements(complete_reqs)
        self.report = self.suggest(detailed_prompt)
        print_in_box(self.report, title="Data Buddy", color="green")

        while True:
            keep_moving = questionary.select("Do you want to continue?", choices=["Yes", "No"]).ask()
            if keep_moving.lower() == "no":
                break

            question = questionary.text("Suggestions to improve the report?").ask()

            with self.console.status("Let me think what else we can do..."):
                self.chat_history.append({"role": "user", "content": question})
                text = self.model.query(
                    self.chat_history,
                    function_call='auto',
                    functions=self.function,
                    response_format={"type": "json_object"}
                )
                self.report = process_report(requirements, json.loads(text))
                self.json_report = json.loads(text)
                print_in_box(self.report, title="Data Buddy", color="green")
                
        self.save_report()
        return self.report

    def format_requirements(self, requirements: dict) -> str:
        """Format requirements into a detailed prompt"""
        return f"""Project Requirements Analysis:
        Task Type: {requirements['task_type']}
        Performance Metrics: {requirements['performance_metric']}
        Constraints: {requirements['constraints']}
        Business Goal: {requirements['business_goal']}
        
        Please provide a comprehensive ML solution addressing these requirements."""