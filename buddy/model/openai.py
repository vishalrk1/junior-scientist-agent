import openai
import json
from typing import Dict, Any, Optional

from buddy.function import get_function, process_function_name, SEARCH_FUNCTIONS

class OpenAIModel:
    def __init__(self, api_key: str, parameters: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.model_name = parameters.get("selected_model", "gpt-4o") if parameters else "gpt-4o"
        self.temperature = parameters.get("temperature", 0.7) if parameters else 0.7
        self.max_tokens = parameters.get("max_tokens", 2000) if parameters else 2000
        self.client = openai.Client(api_key=api_key)
        self.func_call_history = []

    def query(self, chat_history, **kwargs):
        parameters = {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            **kwargs
        }
        
        completion = self.client.chat.completions.create(
            messages=chat_history,
            stream=False,
            **parameters
        )
        
        res = completion.choices[0].message
        if res.function_call:
            function_name = process_function_name(res.function_call.name)
            arguments = json.loads(res.function_call.arguments)
            print("[MLE FUNC CALL]: ", function_name)
            self.func_call_history.append({"name": function_name, "arguments": arguments})
            # avoid the multiple search function calls
            search_attempts = [item for item in self.func_call_history if item['name'] in SEARCH_FUNCTIONS]
            if len(search_attempts) > 3:
                parameters['function_call'] = "none"
            result = get_function(function_name)(**arguments)
            chat_history.append({"role": "assistant", "function_call": dict(res.function_call)})
            chat_history.append({"role": "function", "content": result, "name": function_name})
            return self.query(chat_history, **parameters)
        else:
            return res.content
