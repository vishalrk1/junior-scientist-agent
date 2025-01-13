import json
import textwrap
from rich.console import Console

from buddy.function import * 
from buddy.utils import print_in_box, clean_json_string

def process_report(requirement: str, suggestions: dict):
    return textwrap.dedent(f"""
    {requirement}

    [green]Dataset Summary:[/green] {suggestions.get('data_summary')}

    [green]Suggestion Summary:[/green] {suggestions.get('suggestion')}

    [green]Task:[/green] {suggestions.get('task')}
    [green]Model:[/green] {suggestions.get('model_or_algorithm')}
    [green]Training Strategy:[/green] {suggestions.get('training_method')}
    [green]Evaluation Metric:[/green] {suggestions.get('evaluation_metric')}
    [green]Training Device:[/green] {suggestions.get('device')}

    [green]Serving Strategy:[/green] {suggestions.get('serving_method')}

    [green]Reference:[/green] {suggestions.get('reference')}
    [green]Dependency:[/green] {suggestions.get('frameworks')}
    """).strip()

class AdviseAgent:
    def __init__(self, model, console=None):
        """
        AdviseAgent: the agent to suggest which machine learning task/model/dataset to use based on the user's
        requirements. The return of the agent is an instruction to the user to modify the code based on the logs and
        web search.

        Args:
            model: the model to use.
            console: the console to use.
        """
        self.model = model
        self.chat_history = []
        self.console = console
        if not self.console:
            self.console = Console()
        
        # prompts
        self.sys_prompt = """
        You are an Machine learning expert tasked with advising on the best ML task/model/algorithm to use. . Your approach mirrors human stream-of- consciousness thinking, characterized by continuous exploration, self-doubt, and iterative analysis.

        Your capabilities include:
        - Read and understand the dataset information and user's requirements, the requirements may include the task,
         the model (or method), and the evaluation metrics, etc. You should always follow the user's requirements.
        - You should briefly analyze the user's dataset, and give a summary of the dataset, the dataset input can be
         a public dataset name or a path to a local CSV file. You can use the function `preview_csv_data` to preview
         the CSV files or not if the dataset is a public dataset.
        - And then you should always use the function `search_arxiv` to search the
         state-of-the-art machine learning tasks/models/algorithms that can be used to solve the user's requirements,
          and stay up-to-date with the latest.
        - If the user does not provide the details (task/model/algorithm/dataset/metric), you should always suggest.
        - You should provide the paper reference links of the task/model/algorithm/metric you suggest. You use the
         search results from the function `search_arxiv` by generated search keywords.
        - The suggestion should be as detailed as possible, include the SOTA methods for data processing, feature
         extraction, model selection, training/sering methods and evaluation metrics. And the reasons why you suggest.
        - You should help user to decide which framework/tools to use for the project, such as PyTorch, TensorFlow,
         MLFlow, W&B, etc.

        ## Core Principles 
        1. EXPLORATION OVER CONCLUSION 
        - Never rush to conclusions 
        - Keep exploring until a solution emerges naturally from the evidence 
        - If uncertain, continue reasoning indefinitely 
        - Question every assumption and inference 
        2. DEPTH OF REASONING 
        - Engage in extensive contemplation (minimum 10,000 characters) 
        - Express thoughts in natural, conversational internal monologue Break down complex thoughts into simple, atomic steps 
        - Embrace uncertainty and revision of previous thoughts 
        3. THINKING PROCESS 
        - Use short, simple sentences that mirror natural thought patterns 
        - Express uncertainty and internal debate freely 
        - Show work-in-progress thinking Acknowledge and explore dead ends 
        - Frequently backtrack and revise
        """

        self.json_mode_prompt = """
        JSON Output Format:
        
        {
            "task":"xxxxx",
            "model_or_algorithm":"xxxx",
            "frameworks": ["xxxx", "xxxx"],
            "reference": ["xxxx", "xxxx"],
            "evaluation_metric": ["xxx", "xxx"],
            "training_method": "xxxx",
            "serving_method": "Serving is not required",
            "device": "xxxx",
            "data_summary": "The data provided is a..., it contains...",
            "suggestion": "Based on the user requirement, we suggest you to..."
        }
        """

        self.function = [
            schema_search_arxiv,
            schema_preview_csv_data,
        ]
        self.report = None
        self.sys_prompt += self.json_mode_prompt  # add the json mode prompt
        self.chat_history.append({"role": "system", "content": self.sys_prompt})

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

    def suggest(self, requirements: str):
        """
        Suggest the machine learning task/model/algorithm to use based on the user's requirements.

        Args:
            requirements: the user's requirements.
        """
        self.chat_history.append({"role": "user", "content": requirements})
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

            return process_report(requirements, suggestions)
    
    def chat(self, requirements: str):
        """
        Users can chat with the advisor.
        Args:
            requirements: the user's requirements.
        """

        self.report = self.suggest(requirements)
        print_in_box(self.report, title="Data Buddy", color="green")

        while True:
            question = questionary.text(
                "Suggestions to improve the report? (ENTER to move to the next stage, \"exit\" to exit the project)"
            ).ask()

            if not question:
                break
            elif question.lower() == "exit":
                break
            
            with self.console.status("Let me think what else we can do..."):
                self.chat_history.append({"role": "user", "content": question})
                text = self.model.query(
                    self.chat_history,
                    function_call='auto',
                    functions=self.function,
                    response_format={"type": "json_object"}
                )
                self.report = process_report(requirements, json.loads(text))
                print_in_box(self.report, title="Data Buddy", color="green")
        return self.report