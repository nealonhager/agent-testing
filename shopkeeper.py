from agent import Agent


def get_function_info(obj) -> dict:
    # func_names = [func for func in dir(obj) if callable(obj.__getattribute__(func))]

    # x = dict()
    # for func_name in func_names:
    #     x[func_name] = obj.__getattribute__(func_name).__code__.co_varnames[1:obj.__getattribute__(func_name).__code__.co_argcount]

    # return x

    return {
        func_name: shopkeeper.__getattribute__(func_name).__code__.co_varnames[
            1 : shopkeeper.__getattribute__(func_name).__code__.co_argcount
        ]
        for func_name in dir(shopkeeper)
        if not func_name.startswith("_")
        and callable(shopkeeper.__getattribute__(func_name))
    }


if __name__ == "__main__":
    shopkeeper = Agent(
        task=(
            "Please simulate being a medieval shopkeeper. "
            "You sell potions, and nothing else. If someone asks to buy something else, refer them to someone else. "
            "If someone wants to sell you something, only accept potions."
        ),
        backstory="You are an AI that simulates dialog in an medieval setting.",
    )
    shopkeeper.add_assistant_message(
        "Hello there, I am Sheldon, what kind of potions are you looking for today?"
    )
    print(get_function_info(shopkeeper))
    # print(shopkeeper.messages[-1])
    # print(
    #     {
    #         func_name: shopkeeper.__getattribute__(func_name).__code__.co_varnames[
    #             1 : shopkeeper.__getattribute__(func_name).__code__.co_argcount
    #         ]
    #         for func_name in dir(shopkeeper)
    #         if not func_name.startswith("_")
    #         and callable(shopkeeper.__getattribute__(func_name))
    #     }
    # )
    # shopkeeper.add_user_message(input("> "))
    # print(shopkeeper.execute_task())
