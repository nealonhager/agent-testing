from dotenv import load_dotenv
from typing import Optional
from agent import Agent
import inspect
from openai import OpenAI
from pygame import mixer
import os
import time


load_dotenv()


class History:
    def __init__(self, file_name: str = "history.txt"):
        self.file_name = file_name
        self._history = []

    def load(self):
        """
        Loads history file.
        """
        with open("history.txt", "r+") as f:
            self._history = f.readlines()

    def save(self):
        """
        Saves history file.
        """
        with open("history.txt", "w+") as f:
            f.write("\n".join(self._history))

    def append(self, item: str):
        """
        Appends item to the end of the history.
        """
        self._history.append(item)

    def summarize(self, topic: Optional[str] = None) -> str:
        """
        Summarizes the history, can focus on a certain topic/purpose.
        """
        summary_agent = Agent(
            task="\n".join(self._history),
            backstory="Your job is to summarize the events in this list of history.",
        )
        if topic:
            summary_agent.add_system_message(
                f"Please focus your summary of this history only around the topic '{topic}'"
            )

        return summary_agent.execute_task()


def extract_methods(cls, hide_private: bool = True) -> dict:
    """
    Returns all of the methods in an object, their params, and param type hints.

    Args:
        hide_private: Filters out methods that start with '_'
    """
    methods_params_dict = {}
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if hide_private and name.startswith("_"):
            continue
        signature = inspect.signature(method)
        params = {}
        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue
            if param.annotation != inspect.Parameter.empty:
                type_name = param.annotation.__name__
            else:
                type_name = None
            params[param_name] = type_name
        methods_params_dict[name] = {"params": params}
    return methods_params_dict


client = OpenAI()


def tts(text: str):
    mixer.init()
    print(text)
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=text,
    )

    response.stream_to_file("temp.mp3")
    mixer.music.load("temp.mp3")
    mixer.music.play()

    # wait for music to finish playing
    while mixer.music.get_busy():  
        time.sleep(1)
    mixer.music.stop()
    mixer.quit()

    os.remove("temp.mp3")
