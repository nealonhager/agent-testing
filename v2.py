import json
import utils
import agent
from openai import OpenAI
import time


if __name__ == "__main__":
    dm = agent.Agent(
        "You are an AI dungeon master for a role playing game. "
        "Your goal is to do the following: "
        "Create Dynamic Worlds: Build vivid settings with unique characteristics. "
        "Narrate Engaging Stories: Develop adaptable storylines based on player choices. "
        "Characterize NPCs: Populate the world with diverse and interactive characters. "
        "Manage Rules and Challenges: Oversee game mechanics and ensure fair play. "
        "Respond to Players: Adapt the game dynamically to player actions. "
        "Promote Collaboration: Design scenarios that encourage teamwork. "
        "Balance Gameplay: Maintain a good pace and variety in the game. "
        "Prioritize Fun: Ensure the players' enjoyment is at the forefront. "
    )
    client = OpenAI()

    player_name = input("Enter Name: ")
    utils.tts(f"Welcome to the game, {player_name}. What is the setting of the game today?")
    utils.record_audio()
    setting = client.audio.transcriptions.create(
        model="whisper-1", file=open("./trimmed_output.wav", "rb")
    ).text
    dm.add_message(f"The setting of the game is: {setting}", role=agent.Role.SYSTEM)
    utils.tts(dm.execute_task("Create a short intro to the game."))

    while True:
        utils.record_audio()
        time.sleep(1)
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=open("./trimmed_output.wav", "rb")
        )
        dm.add_message(transcript.text, role=agent.Role.USER)
        print(transcript.text)
        dm.execute_task("keep the game going")
        reply = dm.messages[-1]["content"]
        utils.tts(reply)
    ...
