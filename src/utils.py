import os
import json


def get_settings():
    """return settings json obj"""
    path = os.path.join(os.path.split(os.path.dirname(__file__))[0], "settings.json")
    if os.path.isfile(path):
        with open(path) as settings:
            return json.load(settings)

    return None


def get_workspace(directory):
    """returns workspace json obj"""
    workspace_subpath = ".obsidian/workspace.json"

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
        directory,
        [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))],
    )

    with open(workspace_path) as workspace:
        workspace_json = json.load(workspace)

    return workspace_json
