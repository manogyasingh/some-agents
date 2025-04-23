import json
import re
from typing import Dict, List, Any, Callable, Optional
import anthropic

class ClaudeAgent:
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.system_prompt = (
            "You are a helpful AI assistant with access to tools. "
            "When you need to use a tool, format your response as:\n"
            "```tool\n{\"tool_name\": \"name\", \"parameters\": {\"param1\": \"value1\"}}\n```\n"
            "After receiving the tool's output, continue the conversation."
        )

    def register_tool(self, name: str, description: str, parameters: Dict[str, Dict[str, Any]], handler: Callable):
        self.tools[name] = {"description": description, "parameters": parameters, "handler": handler}
        tools_description = "\n\nAvailable tools:\n"
        for tool_name, tool_info in self.tools.items():
            tools_description += f"- {tool_name}: {tool_info['description']}\n"
            tools_description += f"  Parameters: {json.dumps(tool_info['parameters'])}\n"
        self.system_prompt = (
            "You are a helpful AI assistant with access to tools. "
            "When you need to use a tool, format your response as:\n"
            "```tool\n{\"tool_name\": \"name\", \"parameters\": {\"param1\": \"value1\"}}\n```\n"
            "After receiving the tool's output, continue the conversation."
            f"{tools_description}"
        )

    def _extract_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        tool_pattern = r"```tool\n(.*?)```"
        matches = re.findall(tool_pattern, text, re.DOTALL)
        tool_calls = []
        for match in matches:
            try:
                tool_calls.append(json.loads(match.strip()))
            except json.JSONDecodeError:
                pass
        return tool_calls

    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> str:
        tool_name = tool_call.get("tool_name")
        parameters = tool_call.get("parameters", {})
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found."
        try:
            return self.tools[tool_name]["handler"](**parameters)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    def chat(self, user_input: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        if conversation_history is None:
            conversation_history = []
        messages = conversation_history.copy() + [{"role": "user", "content": user_input}]
        response = self.client.messages.create(model=self.model, system=self.system_prompt, messages=messages, max_tokens=2000)
        assistant_response = response.content[0].text
        tool_calls = self._extract_tool_calls(assistant_response)
        if not tool_calls:
            return assistant_response
        for tool_call in tool_calls:
            tool_call_text = f"```tool\n{json.dumps(tool_call)}\n```"
            text_before_tool = assistant_response.split(tool_call_text)[0]
            tool_result = self._execute_tool_call(tool_call)
            updated_messages = messages + [
                {"role": "assistant", "content": text_before_tool + tool_call_text},
                {"role": "user", "content": f"Tool result: {tool_result}"}
            ]
            final_response = self.client.messages.create(model=self.model, system=self.system_prompt, messages=updated_messages, max_tokens=2000)
            assistant_response = final_response.content[0].text
        return assistant_response
