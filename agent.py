from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import logging
from enum import Enum


load_dotenv()
logging.basicConfig(filename=".log", filemode="w+", level=logging.INFO)


class Role(str, Enum):
    SYSTEM = "system"
    USER = "system"
    ASSISTANT = "system"
    TOOL = "system"


class Agent:
    def __init__(self, backstory: str):
        self.backstory = backstory
        self._client = OpenAI()
        self.messages = []
        self.add_message(backstory, role=Role.SYSTEM)

    def execute_task(self, task: str, role: Role = Role.SYSTEM) -> str:
        """
        Generates a response from the model, adds the response to the message history.
        """
        self.add_message(task, role=role)
        while True:
            try:
                completion = self._client.chat.completions.create(
                    model=os.getenv("GPT_MODEL"),
                    messages=self.messages,
                )

                response = completion.choices[0].message.content
                self.add_message(response, role=Role.ASSISTANT)
                return response
            except Exception as e:
                logging.warning("There was a problem generating a response. Retrying.")

    def add_message(self, message: str, role: Role):
        """
        Adds a new message to the message history.
        """
        new_message = {"role": role, "content": message}
        logging.info(new_message)
        self.messages.append(new_message)


def execute_lone_task(task: str):
    client = OpenAI()
    try:
        completion = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"),
            messages=[
                {
                    "role": "system",
                    "content": "Please just reply to the users request. The user knows you are an AI and referencing it just gets annoying. it would be polite to only speak when spoken to.",
                },
                {"role": "user", "content": task},
            ],
        )

        response = completion.choices[0].message.content
        return response
    except Exception as e:
        logging.warning("There was a problem generating a response. Retrying.")


class FunctionCallingAgent(Agent):
    def __init__(self, task: str, backstory: str, tools: list, function_map: dict):
        super().__init__(task=task, backstory=backstory)
        self.tools = tools
        self.function_map = function_map

    def execute_task(self) -> list:
        """
        Calls function suggested by the model. Returns the result of the function call.
        """
        while True:
            try:
                completion = self._client.chat.completions.create(
                    model=os.getenv("GPT_MODEL"),
                    messages=self.messages,
                    tools=self.tools,
                    tool_choice="auto",
                )

                tool_calls = completion.choices[0].message.tool_calls
                function_responses = []
                if tool_calls:
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_to_call = self.function_map[function_name]
                        function_args = json.loads(tool_call.function.arguments)
                        function_response = function_to_call(
                            start=function_args.get("start"),
                        )
                        function_responses.append(function_response)
                return function_responses
            except Exception as e:
                logging.warning("There was a problem generating a response. Retrying.")
