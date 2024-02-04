from agent import Agent, Role
import json
from utils import extract_methods, tts, record_audio, History
from collections import defaultdict
from log import log
import random
from openai import OpenAI
import time


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
        log.info(f"New character created: {self.name}")

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
        log.info(f"sold {self.in_conversation_with}: {item} for {price} gold")
        self.say(message=f"Thanks, enjoy the {item}, do come again.")

    def gift_item(self, item: str):
        self.inventory.remove(item)
        log.info(f"Gifted {self.in_conversation_with}: {item}")

    def buy_item(self, item: str, price: int):
        self.inventory.append(item)
        self.gold -= price
        log.info(f"{self.name} bought {item} for {price} gold")
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
                    log.info(f"calling {func_name}({func_args})")
                    self.__getattribute__(func_name)(**func_args)
                    log.info(f"called {func_name}({func_args})")
                else:
                    self.say(completion.choices[0].message.content)
                break
            except Exception as e:
                log.warning("Failed to call a function or reply.")


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
            dialog=json.dumps(
                character.conversation_history[character.in_conversation_with]._history
            ),
        )


def create_new_characters(known_characters: list, dialog: str):
    x = Agent(
        "Please look at the dialog and list of characters, and return only new characters."
    )
    x.add_message(
        json.dumps({"dialog": "bobby ate cake with peter", "characters": ["peter"]}),
        role=Role.SYSTEM,
    )
    x.add_message(
        "Bobby",
        role=Role.ASSISTANT,
    )
    x.add_message(
        json.dumps(
            {"dialog": "bobby and randall ate cake with peter", "characters": ["peter"]}
        ),
        role=Role.SYSTEM,
    )
    x.add_message(
        "Bobby,Randall",
        role=Role.ASSISTANT,
    )
    x.add_message(
        json.dumps(
            {
                "dialog": "bobby and randall ate cake with peter",
                "characters": ["peter", "randall", "peter"],
            }
        ),
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
    new_characters = [nc.strip() for nc in new_characters if nc]

    for c in new_characters:
        known_characters.append(
            Character(
                c,
                "You have no specific task at the moment.",
                (
                    f"You simulate being a medieval character named {c}. "
                    f"You talk in the first person, from {c}'s POV. "
                ),
            )
        )


if __name__ == "__main__":
    king_edward = Character(
        name="King Edward",
        task="Protect the kingdom and lead it to prosper.",
        backstory=(
            "You simulate being a medieval king named Edward. "
            "You talk in the first person, from King Edwards's POV. "
            "King Edward just heard word of a dragon terrorizing some farmers in the outskirts of his kingdom. "
            "Edward called his best knight Nealon to help him. Nealon approaches. "
        ),
    )

    characters = [king_edward]
    have_conversation_with(king_edward, characters)
