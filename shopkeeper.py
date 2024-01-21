from agent import Agent
import json
from utils import extract_methods, tts
from collections import defaultdict
import logging
import random


class Character:
    def __init__(self, name: str, task: str, backstory: str):
        self.name = name
        self.agent = Agent(task=task, backstory=backstory)
        self.inventory = []
        self.gold = 100
        self.conversation_history = defaultdict(list)
        self.in_conversation = False
        self._voice = random.choice(
            ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        )

    def greet(self, character: str):
        self.in_conversation = True
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
        self.in_conversation = False

    def reply(self, character: str, message: str):
        self.agent.add_user_message(message)
        self.conversation_history[character].append(message)
        response = self.agent.execute_task()
        self.conversation_history[character].append(response)

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

    def say(self, character: str, message: str):
        self.agent.add_assistant_message(message)
        self.conversation_history[character].append(message)
        tts(message, self._voice)

    def _confirm_sale(self, character: str, item: str, price: int):
        self.gold += price
        logging.info(f"sold {character}: {item} for {price} gold")
        self.say(
            character=character, message=f"Thanks, enjoy the {item}, do come again."
        )
        self.in_conversation = False

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


if __name__ == "__main__":
    shopkeeper = Character(
        name="Shopkeeper Sheldon",
        task="Try and get the user to buy a potion you have in stock.",
        backstory=(
            "You simulate being a medieval shopkeeper named Shopkeeper Sheldon. "
            "You sell potions, and nothing else. If someone asks to buy something else, refer them to someone else. "
            "If someone wants to sell you something, only accept potions. "
            "You should tell someone how much something costs before finalizing the sale. "
            "You talk in the first person, from the shopkeeper's POV."
        ),
    )
    # gamekeeper = Character(
    #     name="Say when the conversation between Shopkeeper Sheldon and Nealon is over.",
    #     task="Try and get the user to buy a potion you have in stock.",
    #     backstory=(
    #         "You keep track of a roleplaying game. "
    #         "Say only 'Complete' when the conversation is over."
    #     ),
    # )
    shopkeeper.greet("Nealon")
    while shopkeeper.in_conversation:
        shopkeeper.react(input("> "))
    # questgiver = Character(
    #     name="Sir Quentin",
    #     task="Lead the village.",
    #     backstory=(
    #         "You simulate being a medieval lord named Sir Quentin. "
    #         "You look over the village, protecting the people and governing them. "
    #         "You talk in the first person, from Sir Quentin's POV."
    #     ),
    # )
    # peasant = Character(
    #     name="Peter",
    #     task="Get a job in town.",
    #     backstory=(
    #         "You simulate being a medieval peasant named Peter. "
    #         "You work the fields in the day, and drink in the tavern at night. "
    #         "You talk in the first person, from Peter's POV."
    #     ),
    # )
    # x = shopkeeper.greet("Peter")
    # for _ in range(5):
    #     x = ("Sir Quentin", x)
    #     questgiver.reply("Peter", x)
