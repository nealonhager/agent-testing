import pytest
import os
from agent import Agent


def delete_file(file_name: str):
    try:
        os.remove(file_name)
    except FileNotFoundError:
        print(f"File not found: {file_name}")


@pytest.fixture
def agent1():
    agent = Agent()
    yield agent


def test_save_agent(agent1):
    agent1.save()
    expected_file_name = agent1.identifier + ".json"
    assert expected_file_name in os.listdir(".")
    delete_file(agent1.identifier + ".json")


def test_load_agent(agent1):
    agent1.save()
    agent2 = Agent.load(agent1.identifier + ".json")
    assert str(agent1) == str(agent2)

    delete_file(agent1.identifier + ".json")
