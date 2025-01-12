import openai
import json

from buddy.function import get_function, process_function_name, SEARCH_FUNCTIONS

class OpenAIModel:
    def __init__(self, model, api_key, temperature=0.7):
        self.model = model if model else "gpt-4o-mini"
        self.api_key = api_key
        self.temperature = temperature
        self.client = openai.Client(model=model, api_key=api_key)
    
    def query(self, chat_history, **kwargs):
        parameters = kwargs
        completion = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
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
        