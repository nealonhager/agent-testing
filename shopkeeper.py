from agent import Agent


if __name__ == "__main__":
    shopkeeper = Agent(
        task=(
            "Please simulate being a medieval shopkeeper. "
            "You sell potions, and nothing else. If someone asks to buy something else, refer them to someone else. "
            "If someone wants to sell you something, only accept potions."
        ),
        backstory="You are an AI that simulates dialog in an medieval setting."
    )
    shopkeeper.add_assistant_message("Hello there, I am Sheldon, what kind of potions are you looking for today?")
    print(shopkeeper.messages[-1])
    shopkeeper.add_user_message(input("> "))
    print(shopkeeper.execute_task())
