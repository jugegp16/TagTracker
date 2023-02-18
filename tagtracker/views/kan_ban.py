from setup import view, Workspace, bcolors


@view
def kanBan(workspace: Workspace):
    print(f"{bcolors.GREY}\tCreating Kanban")

    phases = ["to-do", "in-progress", "finished"]

    if workspace.options and "options" in workspace.options:
        phases = workspace.options["options"]

    output = ""

    for tag, file_paths in sorted(
        filter(lambda i: i[0] in phases, workspace.tags.items()),
        key=lambda i: phases.index(i[0]),
    ):
        if not file_paths:
            continue

        title = " ".join(map(lambda i: i.capitalize(), tag.split("-")))
        output += f"\n\n### {title}\n- " + "\n- ".join(file_paths)

    return output
