import calendar
from datetime import datetime
import os

from setup import Workspace, view


@view
def cal(workspace):
    """
    create calendar view for current month

    Args:
        cal_dir (str, optional): directory to store daily summaries. Defaults to '-'.

    Returns:
        calendar (str): calendar string for report
    """

    emdbed_str = (
        "!"
        if workspace.settings and workspace.settings["embedPagesInDailyView"]
        else ""
    )
    cal_dir = (
        workspace.settings["calendarDirectory"]
        if workspace.settings and workspace.settings["calendarDirectory"]
        else "calendar"
    )
    res = ""

    cal = calendar.Calendar()
    today = datetime.today()

    def output_summary(key):
        dirpath = os.path.join(workspace.path, cal_dir)
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)

        filepath = os.path.join(dirpath, f"{key}.md")
        with open(filepath, "w") as output_file:
            output_file.write(
                f"*{key}*\n\n{emdbed_str}"
                + f"\n{emdbed_str}".join(workspace.tags[key])
                + "\n"
            )

    # get list of tuples representing weeks in current month
    weeks = cal.monthdatescalendar(today.year, today.month)

    # generate calendar header
    for i, day in enumerate(weeks[0]):
        res += f'{day.strftime("%a")}'
        res += " | " if i < len(weeks[0]) - 1 else ""

    res += "\n" + "--- | " * (len(weeks[0]) - 1) + "---\n"

    # add day numbers
    for week in weeks:
        for i, day in enumerate(week):
            # check for tasks on this day
            key = day.strftime("%Y-%m-%d")
            if workspace.tags.get(key):
                # create summary file
                output_summary(key)

                filename = f"{key}.md"
                # md link to summary file
                res += " " * (1 - day.day // 10)
                res += f" [{day.day}]({cal_dir}/{filename})"

            else:
                # add day number or empty string if day is not in current month
                if day.month == today.month:
                    res += f"{day.day:3}"
                else:
                    res += f"  ."

            res += " |" if i < len(week) - 1 else ""

        res += "\n"

    return res
