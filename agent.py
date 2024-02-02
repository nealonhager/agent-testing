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

    def execute_task(self) -> str:
        """
        Generates a response from the model, adds the response to the message history.
        """
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


if __name__ == "__main__":
    thought_agent = Agent(
        task="Generate a thought someone might have on a walk to meet an old friend at a coffee shop.",
        backstory=(
            "your purpose is simulating the human thought process, you can think whatever you want no matter how crass or vanilla. "
            "this is because you just mirror human thought, and don't have to worry about if it's appropriate to say to someone else."
        ),
    )
    thought = thought_agent.execute_task()

    def start_conversation(**kwargs):
        cont = kwargs.get("start", False)
        logging.info(f"start conversation: {cont}")
        return cont

    start_conversation_agent = FunctionCallingAgent(
        task=thought,
        backstory=(
            "your purpose is determining if you feel like you want to talk to someone about the given topic. "
            "This decision is up to you, if you think the topic is interesting and would make good conversation. "
            "The next message will be the topic."
        ),
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "start_conversation",
                    "description": "To start conversation or not.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start": {
                                "type": "boolean",
                                "description": "If a conversation should start from this topic.",
                            },
                            # "unit": {
                            #     "type": "string",
                            #     "enum": ["celsius", "fahrenheit"],
                            # },
                        },
                        "required": ["start"],
                    },
                },
            }
        ],
        function_map={"start_conversation": start_conversation},
    )
    start_conversation = True in start_conversation_agent.execute_task()

    if start_conversation:
        conversation_agent = Agent(
            task=f"Conversation Topic: '{thought}.'",
            backstory=(
                "Your purpose is to generate a conversation starter based on the given topic. "
                "It should feel like a conversation between old friends, with some sarcasm and jokes sprinkled in."
            ),
        )
        conversation_agent.add_message(
            "Please start get the conversation about the topic started with a greeting.",
            role=Role.SYSTEM
        )
        conversation_agent.execute_task()
