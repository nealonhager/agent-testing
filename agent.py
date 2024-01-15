from dotenv import load_dotenv
from openai import OpenAI
import names


load_dotenv()


class Agent:
    def __init__(self):
        self.openai_client = None
        self.identifier = names.get_full_name()

    def _get_openai_client(self) -> OpenAI:
        if self.openai_client is None:
            self.openai_client = OpenAI()
        
        return self.openai_client
        