from typing import Any, Dict, List
from typing import Callable, DefaultDict
import re


class bcolors:
    GREY = "\033[90m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    ENDC = "\033[0m"
    UNDERLINE = "\033[4m"


class Workspace:
    path: str
    tags: DefaultDict[str, List[str]]
    settings: Dict
    filter: str
    options: Any


View = Callable[[Workspace], str]

view_name_pattern = re.compile(r"(?<!^)(?=[A-Z])")

view_options = {}


def view(view: View):
    name = view.__name__

    view_options[name] = view
    view_options[name.lower()] = view
    view_options[view_name_pattern.sub("-", name).lower()] = view
    view_options[view_name_pattern.sub("_", name).lower()] = view

    return view
