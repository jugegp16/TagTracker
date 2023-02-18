import re
from setup import Workspace, bcolors, view


@view
def tagSummary(workspace: Workspace):
    print(f"{bcolors.GREY}\tCreating Tag List")
    res = (
        "\n\n\n----\n*"
        + ", ".join(
            map(
                lambda i: f"{i[0]} ({len(i[1])})",
                sorted(
                    filter(
                        lambda i: not bool(re.search(r"\d{4}-\d{2}-\d{2}", i[0])),
                        workspace.tags.items(),
                    ),
                    key=lambda i: len(i[1]),
                    reverse=True,
                ),
            )
        )
        + "*\n\n"
    )
    return res
