import json
import hashlib
import datetime

import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from typing import List, Dict, Any

@dataclass
class AnalysisResult:
    """Dataclass for storing analysis results"""
    category: str
    steps: str

@dataclass
class AnalysisReport:
    """Dataclass for storing analysis report"""
    dataset_hash: str
    timestamp: str
    results: List['AnalysisResult']
    metadata: Dict[str, Any]

class AnalyzerAgent:
    def __init__(self, model, console=None, reports_dir="analysis_reports"):
        """
        AnalyzerAgent: An agent that can analyze data using a model.

        Args:
            model (Model): A model that can analyze data.
            console (Console): A console to use for input/output.
        """

        self.model = model
        self.console = console if console else Console()
        self.analyze_types = ["data_cleaning", "business_insights"]
        self.report_dir = Path(reports_dir)
        self.report_dir.mkdir(exist_ok=True)

        self.prompts = {
            "data_cleaning": """
            <contemplator>
            Let me analyze this dataset for cleaning needs by considering:
            1. Missing data patterns and their implications
            2. Data quality issues and potential solutions
            3. Outlier detection and handling strategies
            4. Necessary transformations and their impact
            5. Data validation requirements
            
            Walk me through your complete analysis of these aspects.
            </contemplator>
            """,
            
            "business_insights": """
            <contemplator>
            Analyze this data for business value by exploring:
            1. Key patterns and their business implications
            2. Strategic opportunities revealed by the data
            3. Potential risks and mitigation strategies
            4. Actionable recommendations for business growth
            5. Critical metrics for ongoing monitoring
            
            Provide detailed insights with supporting evidence.
            </contemplator>
            """,
        }

    def create_system_prompt(self, df: pd.DataFrame, selected_columns: List[str] = None) -> str:
        """Creates detailed system prompt with focus on selected columns if specified"""
        analysis_cols = selected_columns if selected_columns else df.columns
        
        # Generate detailed statistics for selected columns
        stats = {
            col: {
                "type": str(df[col].dtype),
                "unique_values": df[col].nunique(),
                "missing_values": int(df[col].isnull().sum()),
                "statistics": df[col].describe().to_dict() if df[col].dtype in ['int64', 'float64'] else None
            } for col in analysis_cols
        }
        
        return f"""You are an AI that performs thorough data analysis through self-questioning reasoning.
        
        Dataset Overview:
        - Total Records: {len(df)}
        - Analyzed Columns: {', '.join(analysis_cols)}
        - Column Statistics: {json.dumps(stats, indent=2)}
        
        Approach your analysis with:
        1. Deep exploration of patterns and relationships
        2. Critical questioning of assumptions
        3. Practical business implications
        4. Clear, actionable recommendations
        
        Express your thoughts naturally, showing your reasoning process."""
    
    def get_model_response(self, system_prompt: str, user_prompt: str) -> str:
        """Get response from the model"""
        try:
            response = self.model.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            self.console.print(f"[red]Error getting model response: {str(e)}")
            return f"Error in analysis: {str(e)}"
    
    def generate_dataset_hash(self, df: pd.DataFrame) -> str:
        """Generate a unique hash for the dataset"""
        data_hash = hashlib.md5()
        # Include column names, data types, and basic stats in hash
        data_hash.update(str(df.columns.tolist()).encode())
        data_hash.update(str(df.dtypes.tolist()).encode())
        data_hash.update(str(df.describe().to_dict()).encode())
        return data_hash.hexdigest()
    
    def display_report(self, report: AnalysisReport) -> None:
        """Display analysis report in CLI with rich formatting"""
        self.console.print(Panel(
            f"[bold blue]Analysis Report[/bold blue]\n"
            f"Generated: {report.timestamp}\n"
            f"Dataset Hash: {report.dataset_hash}",
            title="Report Information"
        ))

        # Display metadata
        metadata_table = Table(title="Dataset Metadata")
        metadata_table.add_column("Property", style="cyan")
        metadata_table.add_column("Value", style="yellow")
        
        for key, value in report.metadata.items():
            metadata_table.add_row(str(key), str(value))
        
        self.console.print(metadata_table)
        self.console.print("\n")

        # Display analysis results
        for result in report.results:
            content = f"# {result.category.title()}\n\n{result.steps}\n"
            
            self.console.print(Panel(
                Markdown(content),
                title=f"[bold]{result.category.title()}[/bold]",
                border_style="blue"
            ))
            self.console.print("\n")


    def analyze_data(self, df: pd.DataFrame) -> str:
        """
        Analyze the data with caching support.
        
        Args:
            df: The dataframe to analyze
        """
        # Generate a unique hash for the dataset
        data_hash = self.generate_dataset_hash(df)

        results = []
        system_prompts = self.create_system_prompt(df)

        with self.console.status("Analyzin and getting insights on the data....") as status:
            for analysis_type in self.analyze_types:
                status.update(f"[bold green]Performing {analysis_type} analysis...")
                chat_history = [
                    {"role": "system", "content": system_prompts},
                    {"role": "user", "content": self.prompts[analysis_type]}
                ]

                # Get model response for the analysis type
                insights = self.model.query(chat_history)
                results.append(AnalysisResult(analysis_type, insights))

                self.console.print(f"[green]✓[/green] Completed {analysis_type} analysis")

        # Create an analysis report
        report = AnalysisReport(
            dataset_hash=data_hash,
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            results=results,
            metadata={
                "rows": len(df),
                "columns": len(df.columns),
                "memory_usage": df.memory_usage(deep=True).sum() / 1024**2,  # MB
                "dtypes": df.dtypes.value_counts().to_dict()
            },
        )

        self.display_report(report=report)

        return report