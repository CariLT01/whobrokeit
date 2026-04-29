from typing import TypedDict
from rich.prompt import Prompt

class PromptOption(TypedDict):
    option_text: str
    option_name: str

def prompt_select(*, title: str, options: list[PromptOption]) -> str:
    result = Prompt.ask(
        title,
        choices=[
            option["option_text"] for option in options
        ],
        default=options[0]["option_text"]
    )
    
    # map back
    option_name = None
    for option in options:
        if option["option_text"] == result:
            option_name = option["option_name"]
    
    if option_name == None:
        raise ValueError("cannot find option name")
    
    return option_name
    
    