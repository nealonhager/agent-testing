from agent import Agent
import json
from utils import extract_methods, tts, record_audio
from collections import defaultdict
import logging
import random
from openai import OpenAI
import time


class Character:
    def __init__(self, name: str, task: str, backstory: str):
        self.name = name
        self.agent = Agent(backstory=backstory + task)
        self.inventory = []
        self.gold = 100
        self.conversation_history = defaultdict(list)
        self.in_conversation_with = False
        self._voice = random.choice(
            ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        )

    def greet(self, character: str):
        self.in_conversation_with = character
        if character not in self.conversation_history:
            self.agent.add_system_message(
                "You greet a character you haven't met before, what do you say?"
            )
        else:
            self.agent.add_system_message(
                f"You greet a character named {character}, what do you say?"
            )

        response = self.agent.execute_task()
        self.conversation_history[character].append(response)

        tts(response, self._voice)

        return response

    def stop_conversation(self):
        self.in_conversation_with = None

    def reply(self, message: str):
        self.agent.add_user_message(message)
        self.conversation_history[self.in_conversation_with].append(message)
        response = self.agent.execute_task()
        self.conversation_history[self.in_conversation_with].append(response)

        tts(response, self._voice)

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "stop_conversation",
                    "description": "Signals character that conversation can end.",
                },
            }
        ]
        try:
            completion = self.agent._client.chat.completions.create(
                model="gpt-4",
                messages=self.agent.messages,
                tools=tools,
                tool_choice="auto",
            )
            func_info = completion.choices[0].message.tool_calls[0].function
            func_name = func_info.name
            func_args = json.loads(func_info.arguments)
            self.__getattribute__(func_name)(**func_args)
        except Exception as e:
            pass

        return response

    def say(self, message: str):
        self.agent.add_assistant_message(message)
        self.conversation_history[self.in_conversation_with].append(message)
        tts(message, self._voice)

    def _confirm_sale(self, item: str, price: int):
        purchased = input(f"Purchase {item} for {price}? (y/N)").strip().lower() == "y"
        if not purchased:
            self.react(f"{self.in_conversation_with} rejected the purchase.")
            return
        self.gold += price
        logging.info(f"sold {self.in_conversation_with}: {item} for {price} gold")
        self.say(message=f"Thanks, enjoy the {item}, do come again.")
        self.in_conversation_with = None

    def attack(self):
        print("ATTACK!")

    def use_potion(self, potion_name:str):
        print(f"use potion {potion_name}")

    def react(self, action: str):
        tools = extract_methods(type(self))
        tools = {tool: params for tool, params in tools.items() if tool != "react"}
        self.agent.add_system_message(
            f"{action} What do you, {self.name} , do? Please use a tool i've given you."
        )

        formatted_tools = []
        for func_name, params in tools.items():
            formatted_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": func_name,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                name: {"type": type_}
                                for name, type_ in params["params"].items()
                            },
                        },
                        "required": list(params["params"].keys()),
                    },
                }
            )

        while True:
            try:
                completion = self.agent._client.chat.completions.create(
                    model="gpt-4",
                    messages=self.agent.messages,
                    tools=formatted_tools,
                    tool_choice="auto",
                )
                func_info = completion.choices[0].message.tool_calls[0].function
                func_name = func_info.name
                func_args = json.loads(func_info.arguments)
                self.__getattribute__(func_name)(**func_args)
                logging.info(f"called {func_name}({func_args})")
                break
            except Exception as e:
                logging.warning("Could not find a function to call.")


def have_conversation_with(character: Character):
    character.greet("Nealon")
    _client = OpenAI()
    while character.in_conversation_with is not None:
        record_audio()
        time.sleep(1)
        transcript = _client.audio.transcriptions.create(
            model="whisper-1", file=open("./trimmed_output.wav", "rb")
        )
        character.react(f'Nealon says: "{transcript.text}"')


if __name__ == "__main__":
    shopkeeper = Character(
        name="Shopkeeper Sheldon",
        task="Try and get the user to buy a potion you have in stock.",
        backstory=(
            "You simulate being a medieval shopkeeper named Shopkeeper Sheldon. "
            "You sell potions, and nothing else. If someone asks to buy something else, refer them to someone else. "
            "If someone wants to sell you something, only accept potions. "
            "You should tell someone how much something costs before finalizing the sale. "
            "You talk in the first person, from the shopkeeper's POV. "
            "You are eccentric, and find the humor in everything. "
            "If attacked, you can use your potions. "
        ),
    )
    questgiver = Character(
        name="Sir Quentin",
        task="Lead the village.",
        backstory=(
            "You simulate being a medieval lord named Sir Quentin. "
            "You rule over the village, protecting the people and governing them. "
            "You talk in the first person, from Sir Quentin's POV."
        ),
    )
    peasant = Character(
        name="Peter",
        task="Get a job in town.",
        backstory=(
            "You simulate being a medieval peasant named Peter. "
            "You work the fields in the day, and drink in the tavern at night. "
            "You talk in the first person, from Peter's POV."
        ),
    )
    characters = [shopkeeper, questgiver, peasant]
    have_conversation_with(questgiver)
