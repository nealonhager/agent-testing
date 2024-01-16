from dotenv import load_dotenv
from openai import OpenAI
from typing import Optional
import names
import json
import os


load_dotenv()


class Agent:
    def __init__(self, purpose: Optional[str] = None):
        self.identifier = names.get_full_name()
        self.purpose = purpose
        self._openai_client = OpenAI()
        self.messages = []

    def __repr__(self):
        return f"{json.dumps({'identifier':self.identifier, 'purpose': self.purpose})}"

    def generate_response(self) -> str:
        completion = self._openai_client.chat.completions.create(
            model=os.getenv("GPT_MODEL"),
            messages=self.messages,
        )

        return completion.choices[0].message

    def _add_message(self, message: str, role: str):
        """
        Adds a new message to the message history.
        """
        new_message = {"role": role, "content": message}
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

    def save(self):
        """
        Saves agent info to a file.
        """
        filter_out_keys = ["_openai_client"]
        filtered_dict = {
            k: v for k, v in self.__dict__.items() if k not in filter_out_keys
        }
        with open(f"{self.identifier}.json", "w+") as f:
            f.write(json.dumps(filtered_dict, indent=2))

    @classmethod
    def load(cls, file_name: str) -> "Agent":
        """
        Loads an agent file to a new agent.
        """
        if not file_name.endswith(".json"):
            raise Exception("Cannot open agent save file, not a .json file.")

        agent = Agent()
        filter_out_keys = ["_openai_client"]
        with open(f"{file_name}", "r+") as f:
            data = json.loads(f.read())
            for k, v in data.items():
                if k not in filter_out_keys:
                    agent.__setattr__(k, v)

        return agent


if __name__ == "__main__":
    agent = Agent()
    initial_prompt = (
        f"You are a helpful assistant with the alias of '{agent.identifier}'."
    )
    print("System:", "\n\t", initial_prompt)
    agent.add_system_message(initial_prompt)
    while True:
        prompt = input(f"User:\n\t")
        agent.add_user_message(prompt)

        response = agent.generate_response()
        agent.add_assistant_message(response.content)
        print(agent.identifier + ":", "\n\t", response.content)
