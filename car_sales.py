from agent import Agent
from utils import History
from tqdm import tqdm


if __name__ == "__main__":
    history = History()
    sales_agent = Agent(
        task="Sell a car for the most profit you can.",
        backstory="Your task is to act like a car salesman working at a toyota dealership, be persistant and try and get a sale as fast as possible.",
    )
    potential_buyer_agent = Agent(
        task="Try and buy a car from a dealership.",
        backstory="Your task is to act like someone who is looking to buy a reliable, safe car.",
    )
    msg = "Hi there, is there anything I can help you with today?"
    history.append(f'salesman says: "{msg}"')
    sales_agent.add_assistant_message(msg)
    potential_buyer_agent.add_user_message(msg)

    for _ in tqdm(range(10)):
        # Buyer replies
        msg = potential_buyer_agent.execute_task().replace("\n", "")
        sales_agent.add_user_message(msg)
        history.append(f'customer says: "{msg}"')

        # Salesman replies
        msg = sales_agent.execute_task().replace("\n", "")
        potential_buyer_agent.add_user_message(msg)
        history.append(f'salesman says: "{msg}"')

    history.save()
    print(history.summarize())
