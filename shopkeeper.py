from typing import Optional, Union
from agent import Agent
import json
from utils import extract_methods, tts
from collections import defaultdict
from openai import OpenAI


class Character:
    def __init__(self, name: str):
        self.name = name
        self.agent = Agent(
            task="Try and get the user to buy a potion you have in stock.",
            backstory=(
                f"You simulate being a medieval shopkeeper named {self.name}. "
                "You sell potions, and nothing else. If someone asks to buy something else, refer them to someone else. "
                "If someone wants to sell you something, only accept potions. "
                "You talk in the first person, from the shopkeeper's POV."
            ),
        )
        self.inventory = []
        self.gold = 100
        self.conversation_history = defaultdict(list)

    def greet(self, character: str):
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

        tts(response)

        return response

    def reply(self, character: str, message: str):
        self.agent.add_user_message(message)
        self.conversation_history[character].append(message)
        response = self.agent.execute_task()
        self.conversation_history[character].append(response)

        tts(response)

        return response

    def say(self, character: str, message: str):
        self.agent.add_assistant_message(message)
        self.conversation_history[character].append(message)
        tts(message)


    def sell(self, character:str, item: str, price: int):
        self.gold += price
        print(f"sold {character}: {item} for {price} gold")
        self.say(character=character, message=f"Thanks, enjoy the {item}, do come again.")

    def react(self, action: str):
        tools = extract_methods(type(self))
        tools = {tool: params for tool, params in tools.items() if tool != "react"}
        self.agent.add_system_message(f"{action} What do you, {self.name} , do? Please use a tool i've given you.")
        print(tools)

        y = []
        for func_name, params in tools.items():
            y.append(
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
                    tools=y,
                    tool_choice="auto",
                )
                func_info = completion.choices[0].message.tool_calls[0].function
                func_name = func_info.name
                func_args = json.loads(func_info.arguments)
                self.__getattribute__(func_name)(**func_args)
                break
            except Exception as e:
                print("!")



if __name__ == "__main__":
    shopkeeper = Character(name="Shopkeeper Sheldon")
    shopkeeper.react(
        "A stranger buys a health potion for 5 gold."
    )
