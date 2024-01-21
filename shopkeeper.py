from typing import Optional, Union
from agent import Agent
import json
from utils import extract_methods, tts
from collections import defaultdict


class Character:
    def __init__(self, name: str):
        self.name = name
        self.agent = Agent(
            task="Try and get the user to buy a potion you have in stock.",
            backstory=(
                f"You simulate being a medieval shopkeeper named {self.name}. "
                "You sell potions, and nothing else. If someone asks to buy something else, refer them to someone else. "
                "If someone wants to sell you something, only accept potions."
            ),
        )
        self.inventory = []
        self.gold = 100
        self.conversation_history = defaultdict(list)

    def greet(self, character: Union["Character", str], message: Optional[str] = None):
        try:
            character = character.name
        except Exception as _:
            pass

        if character not in self.conversation_history:
            self.agent.add_system_message("You greet a character you haven't met before, what do you say?")
        else:
            self.agent.add_system_message(f"You greet a character named {character}, what do you say?")

        response = self.agent.execute_task()
        self.conversation_history[character].append(response)

        tts(response)

        return response

    def talk(self, character: Union["Character", str], message: str):
        try:
            character = character.name
        except Exception as _:
            pass

        self.agent.add_user_message(message)
        response = self.agent.execute_task()
        self.conversation_history[character].append(response)

        tts(response)

        return response


if __name__ == "__main__":
    shopkeeper = Character(name="Shopkeeper Sheldon")
    # print(json.dumps(extract_methods(Agent), indent=2))
    shopkeeper.greet("Nealon")
    response = input("> ")
    shopkeeper.talk("Nealon", response)
