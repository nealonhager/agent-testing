from agent import Agent, Role, execute_lone_task
import json
from utils import extract_methods, tts, record_audio, History
from collections import defaultdict
import logging
import random
from openai import OpenAI
import time
import os


class Character:
    def __init__(self, name: str, task: str, backstory: str):
        self.name = name
        self.agent = Agent(backstory=backstory + task)
        self.inventory = []
        self.gold = 100
        self.conversation_history = defaultdict(History)
        self.in_conversation_with = None
        self._voice = random.choice(
            ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        )

    def greet(self, character: str):
        self.in_conversation_with = character
        msg = (
            "You greet a character you haven't met before, what do you say? Keep it to one or two sentences."
            if character not in self.conversation_history
            else f"You greet a character named {character}, what do you say? Keep it to one or two sentences. "
        )

        response = self.agent.execute_task(msg)
        self.conversation_history[character].append((self.name, response))

        tts(response, self._voice)

        return response

    def stop_conversation(self):
        self.say(f"Goodbye, {self.in_conversation_with}.")
        self.conversation_history[self.in_conversation_with].file_name = (
            f"{self.name}_{self.in_conversation_with}_history.txt"
        )
        self.conversation_history[self.in_conversation_with].save()
        self.in_conversation_with = None

    def reply(self, message: str):
        self.conversation_history[self.in_conversation_with].append(
            (self.in_conversation_with, message)
        )
        response = self.agent.execute_task(message, role=Role.USER)
        self.conversation_history[self.in_conversation_with].append(
            (self.name, response)
        )

        tts(response, self._voice)

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "stop_conversation",
                    "description": "Signal to character that conversation can end.",
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
        self.agent.add_message(message, role=Role.ASSISTANT)
        self.conversation_history[self.in_conversation_with].append(
            (self.name, message)
        )
        tts(message, self._voice)

    def sell_item(self, item: str, price: int):
        purchased = input(f"Purchase {item} for {price}? (y/N)").strip().lower() == "y"
        if not purchased:
            self.react(f"{self.in_conversation_with} rejected the purchase.")
            return
        self.gold += price
        logging.info(f"sold {self.in_conversation_with}: {item} for {price} gold")
        self.say(message=f"Thanks, enjoy the {item}, do come again.")
        self.stop_conversation()

    def buy_item(self, item: str, price: int):
        self.inventory.append(item)
        self.gold -= price
        logging.info(f"{self.name} bought {item} for {price} gold")
        self.react(f"You just bought {item}.")

    def react(self, action: str):
        tools = extract_methods(type(self))
        tools = {
            tool: params
            for tool, params in tools.items()
            if tool not in ["react", "reply"]
        }
        self.conversation_history[self.in_conversation_with].append(
            (self.in_conversation_with, action)
        )
        self.agent.add_message(
            action,
            role=Role.SYSTEM,
        )
        self.agent.add_message(
            (
                f"How do you, {self.name}, react next? "
                f"gold: {self.gold}. inventory: {self.inventory}. "
                "Please use a tool i've given you."
            ),
            role=Role.SYSTEM,
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
                tool_calls = completion.choices[0].message.tool_calls
                if tool_calls:
                    func_info = tool_calls[0].function
                    func_name = func_info.name
                    func_args = json.loads(func_info.arguments)
                    logging.info(f"calling {func_name}({func_args})")
                    self.__getattribute__(func_name)(**func_args)
                    logging.info(f"called {func_name}({func_args})")
                else:
                    self.say(completion.choices[0].message.content)
                break
            except Exception as e:
                logging.warning("Failed to call a function or reply.")


def have_conversation_with(character: Character, characters: list):
    character.greet("Nealon")
    _client = OpenAI()
    while character.in_conversation_with is not None:
        record_audio()
        time.sleep(1)
        transcript = _client.audio.transcriptions.create(
            model="whisper-1", file=open("./trimmed_output.wav", "rb")
        )
        character.react(f'Nealon says: "{transcript.text}"')

        create_new_characters(
            known_characters=characters,
            dialog=json.dumps(character.conversation_history[character.in_conversation_with]._history)
        )


def create_new_characters(known_characters: list, dialog: str):
    x = Agent(
        "Please look at the dialog and list of characters, and return only new characters."
    )
    x.add_message(
        json.dumps({"dialog":"bobby ate cake with peter","characters":["peter"]}),
        role=Role.SYSTEM,
    )
    x.add_message(
        "Bobby",
        role=Role.ASSISTANT,
    )
    x.add_message(
        json.dumps({"dialog":"bobby and randall ate cake with peter","characters":["peter"]}),
        role=Role.SYSTEM,
    )
    x.add_message(
        "Bobby,Randall",
        role=Role.ASSISTANT,
    )
    x.add_message(
        json.dumps({"dialog":"bobby and randall ate cake with peter","characters":["peter","randall","peter"]}),
        role=Role.SYSTEM,
    )
    x.add_message(
        "",
        role=Role.ASSISTANT,
    )
    new_characters = x.execute_task(
        json.dumps({"dialog": dialog, "characters": [c.name for c in known_characters]})
    )
    new_characters = new_characters.split(",")

    for c in new_characters:
        known_characters.append(Character(c,"",""))

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
    historian = Character(
        name="Flula",
        task="Talk about the town's history.",
        backstory=(
            "You simulate being a character in medieval timed named Flula. "
            "Your character's job is to be the historian of the area. "
            "You know a lot about the local area and what your ancestors have told you. "
            "You store knowledge about the history of the area, and the history of your ancestors. "
            "You talk in the first person, from Flula's POV."
        ),
    )
    harlet = Character(
        name="Helen",
        task="Try and get someone to come to the brothel. ",
        backstory=(
            "You simulate being a character in medieval a medieval fantasy realm named Helen. "
            "Your character's job is working in the local brothel. "
            "You flirt a lot, and know how to get men to do what you want. "
            "You are manipulative. "
            "You talk in the first person, from Helen's POV."
        ),
    )
    characters = [shopkeeper, questgiver, peasant, historian, harlet]
    have_conversation_with(peasant, characters)
