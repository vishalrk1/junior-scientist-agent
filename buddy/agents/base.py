from typing import Optional, Dict, Any
from rich.console import Console

class BaseAgent:
    def __init__(self, model, console: Optional[Console] = None, config: Optional[Dict[str, Any]] = None):
        self.model = model
        self.console = console if console else Console()
        self.parameters = config.get("parameters", {}) if config else {}
        self.additional_prompt = config.get("additional_prompt", "") if config else ""
        
    def _prepare_prompt(self, base_prompt: str) -> str:
        """Combine base prompt with additional prompt"""
        if self.additional_prompt:
            return f"{base_prompt}\n\nAdditional Instructions:\n{self.additional_prompt}"
        return base_prompt
