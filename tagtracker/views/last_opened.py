import os
import json

from setup import view, Workspace, bcolors


@view
def lastOpened(workspace: Workspace):
    """
    create last opened files table for obsidian users

    Returns:
        res (str): last opened files table
    """

    res = ""
    workspace_subpath = ".obsidian/workspace.json"
    workspace_path = None

    def find_workspace(path: os.path, dirs):
        res = None
        for d in map(lambda x: os.path.join(path, x), dirs):
            if ".git" in d:
                continue

            for f in os.listdir(d):
                tmp_path = os.path.join(d, f)
                if os.path.isfile(tmp_path):
                    if workspace_subpath in tmp_path:
                        res = tmp_path
                        break

                else:
                    res = res or find_workspace(d, [f])

        return res

    workspace_path = find_workspace(
        workspace.path,
        [
            f
            for f in os.listdir(workspace.path)
            if os.path.isdir(os.path.join(workspace.path, f))
        ],
    )

    if not workspace_path:
        print(f"{bcolors.WARNING}\tError: No Obsidian workspace.json Detected")
        return res

    with open(workspace_path) as f:
        json_str = json.load(f)

        files = map(
            lambda i: f"[{i.split('/')[-1]}]({i.replace(' ', '%20')})",
            filter(
                lambda filename: os.path.isfile(os.path.join(workspace.path, filename)),
                json_str["lastOpenFiles"],
            ),
        )

        res += "\n\n\n----\n\n**Last Opened**\n- "
        res += "\n- ".join(files)

    return res
