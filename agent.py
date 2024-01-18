from dotenv import load_dotenv
from openai import OpenAI
from typing import Optional
import names
import json
import os
import logging


load_dotenv()
logging.basicConfig(level=logging.INFO)


class Agent:
    def __init__(self, task: str, backstory: str):
        self.task = task
        self.backstory = backstory
        self._client = OpenAI()
        self.messages = []
        self.add_system_message(backstory)
        self.add_user_message(task)

    def generate_response(self) -> str:
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
                self.add_assistant_message(response)
                return response
            except Exception:
                logging.warning("There was a problem generating a response. Retrying.")

    def _add_message(self, message: str, role: str):
        """
        Adds a new message to the message history.
        """
        new_message = {"role": role, "content": message}
        logging.info(new_message)
        self.messages.append(new_message)

    def add_system_message(self, message):
        """
        Adds a new system message to the message history.
        """
        self._add_message(message=message, role="system")

    def add_user_message(self, message):
        """
        Adds a new user message to the message history.
        """
        self._add_message(message=message, role="user")

    def add_assistant_message(self, message):
        """
        Adds a new assistant message to the message history.
        """
        self._add_message(message=message, role="assistant")

    def add_tool_message(self, message):
        """
        Adds a new tool message to the message history.
        """
        self._add_message(message=message, role="tool")


if __name__ == "__main__":
    agent = Agent(
        task="Generate a thought about oranges.",
        backstory="you are an AI with the purpose of simulating the human thought process, you can think whatever you want as you mirror the human thought, not what humans say or do.",
    )
    agent.generate_response()
    print(agent.messages)
