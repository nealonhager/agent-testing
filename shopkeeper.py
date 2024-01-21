import inspect
from agent import Agent
import json


def extract_methods(cls, hide_private: bool = True) -> dict:
    """
    Returns all of the methods in an object, their params, and param type hints.

    Args:
        hide_private: Filters out methods that start with '_'
    """
    methods_params_dict = {}
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if hide_private and name.startswith("_"):
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
            params[param_name] = type_name
        methods_params_dict[name] = {"params": params}
    return methods_params_dict


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
    print(json.dumps(extract_methods(Agent), indent=2))
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
