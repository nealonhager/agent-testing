from typing import Optional
from agent import Agent


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
