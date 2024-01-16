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

    def __repr__(self):
        return f"{json.dumps({'identifier':self.identifier, 'purpose': self.purpose})}"

    def x(self):
        completion = self._openai_client.chat.completions.create(
            model=os.getenv("GPT_MODEL"),
            messages=[
                {
                    "role": "system",
                    "content": f"You are a helpful assistant with the alias of 'f{self.identifier}'.",
                },
                {"role": "user", "content": "Hello, my name is Tim, what's your name?"},
            ],
        )

        print(completion.choices[0].message)

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
