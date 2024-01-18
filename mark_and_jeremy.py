from agent import Agent
from utils import History
from tqdm import tqdm


if __name__ == "__main__":
    history = History()
    mark = Agent(
        task="Convince Jeremy Brexit is a good idea.",
        backstory="Your task is to act like the character Mark from the British comedy tv show \"peep show\" Please try and recreate Mark's speech pattern.",
    )
    jeremy = Agent(
        task="Convince Mark Brexit is a bad idea.",
        backstory="Your task is to act like the character Jeremy (Jez) from the British comedy tv show \"peep show\". Please try and recreate Jeremy's speech pattern.",
    )
    msg = "Hey Jez, did you see that thing on the news about Brexit?"
    history.append(f'Mark says: "{msg}"')
    mark.add_assistant_message(msg)
    jeremy.add_user_message(msg)

    for _ in tqdm(range(10)):
        # Buyer replies
        msg = jeremy.execute_task().replace("\n", "")
        mark.add_user_message(msg)
        history.append(f'Jeremy says: "{msg}"')

        # Salesman replies
        msg = mark.execute_task().replace("\n", "")
        jeremy.add_user_message(msg)
        history.append(f'Mark says: "{msg}"')

    history.save()
    print(history.summarize())
