import pytest
import os
from agent import Agent


@pytest.fixture
def agent1():
    agent = Agent()
    yield agent