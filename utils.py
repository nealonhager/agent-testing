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


def extract_methods(obj, hide_dunder: bool = True) -> dict:
    """
    Returns all of the methods in an object, their params, and param type hints.

    Args:
        hide_dunder: Filters out methods that start with '__'
    """
    methods_params_dict = {}
    for name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
        if hide_dunder and name.startswith("__"):
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
            type_name = "string" if type_name == "str" else type_name
            type_name = "integer" if type_name == "int" else type_name
            type_name = "boolean" if type_name == "bool" else type_name
            params[param_name] = type_name
        methods_params_dict[name] = {"params": params}
    return methods_params_dict


client = OpenAI()


def tts(text: str, voice: str = "onyx"):
    print(text)
    if not int(os.getenv("TTS", 0)):
        return

    mixer.init()
    response = client.audio.speech.create(
        model="tts-1", voice=voice, input=text, speed=1.25
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


import pyaudio
import wave
import keyboard
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

def record_audio():
    # Audio recording parameters
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "output.wav"

    audio = pyaudio.PyAudio()

    # Start recording
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    print("Recording... Press Space Bar to stop.")

    frames = []

    while True:
        data = stream.read(CHUNK)
        frames.append(data)
        if keyboard.is_pressed('space'):
            print("Recording stopped.")
            break

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded data as a WAV file
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

    # Trimming silence
    sound = AudioSegment.from_wav(WAVE_OUTPUT_FILENAME)
    nonsilent_chunks = detect_nonsilent(sound, min_silence_len=500, silence_thresh=-50)
    trimmed_sound = sound[nonsilent_chunks[0][0]:nonsilent_chunks[-1][1]]
    trimmed_sound.export("trimmed_output.wav", format="wav")

    print("Saved trimmed recording to 'trimmed_output.wav'.")

    