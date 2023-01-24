import argparse
import calendar
import json
import os
import re
from collections import defaultdict
from datetime import datetime


class bcolors:
    GREY = "\033[90m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    ENDC = "\033[0m"
    UNDERLINE = "\033[4m"


class TagTracker:
    def __init__(self, directory: str, output_name: str) -> None:
        """
        initialize tag tracker

        Args:
            directory (str): search directory
            output_name (str): output file name
        """

        self.dir = directory
        self.output_name = output_name
        self.tags = defaultdict(list)
        self.phases = ["to-do", "in-progress", "finished"]
        self.settings = None

    def __call__(self):
        """
        analyze directory and output task report
        """

        self.__parse_settings()
        print(f"{bcolors.OKCYAN}Analyzing...")
        self.index(self.dir, set())
        print(f"{bcolors.OKCYAN}Generating Report...")
        self.output()

    def __parse_settings(self):
        """
        parse settings.json and write object to self.settings
        """

        path = os.path.join(
            os.path.split(os.path.dirname(__file__))[0], "settings.json"
        )
        if os.path.isfile(path):
            with open(path) as settings:
                self.settings = json.load(settings)

    def index(self, directory: str, found_files: set):
        """
        find and index tagged files in input directory

        Args:
            directory (str): path to index
            found_files (set): searched file paths
        """

        if not os.path.isdir(directory) or ".git" in directory:
            return

        print(f"{bcolors.GREY}\tSearching {bcolors.UNDERLINE}{directory}{bcolors.ENDC}")

        # search all files in directory
        for root, dirs, files in os.walk(directory):
            for filename in files:

                # open file and read contents
                file_path = os.path.join(root, filename)
                if file_path not in found_files:
                    found_files.add(file_path)

                    # only look at .md files
                    if ".md" not in filename:
                        continue

                    print(
                        f"{bcolors.GREY}\t\tIndexing {bcolors.UNDERLINE}{filename}{bcolors.ENDC}"
                    )

                    with open(file_path, "r") as f:

                        # search for tags using regex
                        contents = f.read()
                        tags = re.findall(r"#\S+", contents)

                        # index tags -> filename
                        for tag in tags:
                            tag = tag[1:]

                            if "#" not in tag:
                                rel_path: str = os.path.relpath(file_path, self.dir)
                                formatted = f"[{file_path.split('/')[-1][:-3]}]({rel_path.replace(' ', '%20')})"
                                self.tags[tag].append(formatted)

            # recursively search subdirectories
            for subdir in dirs:
                self.index(os.path.join(directory, subdir), found_files)

    def calendar(self, cal_dir="-"):
        """
        create calendar view for current month

        Args:
            cal_dir (str, optional): directory to store daily summaries. Defaults to '-'.

        Returns:
            calendar (str): calendar string for report
        """

        res = ""
        cal = calendar.Calendar()
        today = datetime.today()
        emdbed_str = (
            "!" if self.settings and self.settings["embedPagesInDailyView"] else ""
        )

        def output_summary(key):
            dirpath = os.path.join(self.dir, cal_dir)
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath)

            filepath = os.path.join(dirpath, f"{key}.md")
            with open(filepath, "w") as output_file:
                output_file.write(
                    f"*{key}*\n\n{emdbed_str}"
                    + f"\n{emdbed_str}".join(self.tags[key])
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
                if self.tags.get(key):

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

    def last_opened(self):
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
            self.dir,
            [
                f
                for f in os.listdir(self.dir)
                if os.path.isdir(os.path.join(self.dir, f))
            ],
        )

        if not workspace_path:
            print(f"{bcolors.WARNING}\tError: No Obsidian workspace.json Detected")
            return res

        with open(workspace_path) as workspace:
            json_str = json.load(workspace)

            files = map(
                lambda i: f"[{i.split('/')[-1]}]({i.replace(' ', '%20')})",
                filter(
                    lambda filename: os.path.isfile(os.path.join(self.dir, filename)),
                    json_str["lastOpenFiles"],
                ),
            )

            res += "\n\n\n----\n\n**Last Opened**\n- "
            res += "\n- ".join(files)

        return res

    def output(self):
        """
        write report to output file
        """

        with open(os.path.join(self.dir, self.output_name), "w") as output_file:

            # section line
            output_file.write("----\n")

            # calendar
            print(f"{bcolors.GREY}\tCreating Calendar")
            output_file.writelines(self.calendar())

            # phase list
            print(f"{bcolors.GREY}\tCreating Kanban")
            for tag, file_paths in sorted(
                filter(lambda i: i[0] in self.phases, self.tags.items()),
                key=lambda i: self.phases.index(i[0]),
            ):
                if not file_paths:
                    continue

                title = " ".join(map(lambda i: i.capitalize(), tag.split("-")))
                output_file.write(f"\n\n### {title}\n- " + "\n- ".join(file_paths))

            # last opened files
            print(f"{bcolors.GREY}\tCreating Recently Opened")
            output_file.write(self.last_opened())

            # tags
            print(f"{bcolors.GREY}\tCreating Tag List")
            output_file.write(
                "\n\n\n----\n*"
                + ", ".join(
                    map(
                        lambda i: f"{i[0]} ({len(i[1])})",
                        sorted(
                            filter(
                                lambda i: not bool(
                                    re.search(r"\d{4}-\d{2}-\d{2}", i[0])
                                ),
                                self.tags.items(),
                            ),
                            key=lambda i: len(i[1]),
                            reverse=True,
                        ),
                    )
                )
                + "*\n\n"
            )

            print(
                f"{bcolors.OKGREEN}Success!\n",
                f"\t{bcolors.GREY}Wrote Summary to {os.path.join(self.dir, self.output_name)}\n",
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""

        ████████  █████   ██████  ████████ ██████   █████   ██████ ██   ██ ███████ ██████  
           ██    ██   ██ ██          ██    ██   ██ ██   ██ ██      ██  ██  ██      ██   ██ 
           ██    ███████ ██   ███    ██    ██████  ███████ ██      █████   █████   ██████  
           ██    ██   ██ ██    ██    ██    ██   ██ ██   ██ ██      ██  ██  ██      ██   ██ 
           ██    ██   ██  ██████     ██    ██   ██ ██   ██  ██████ ██   ██ ███████ ██   ██ 

                                A Markdown Task Management Tool
        """,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        nargs="?",
        help="directory to search for tagged markdown files\ndefault: current working directory",
        default=os.getcwd(),
    )
    parser.add_argument(
        "-o",
        "--output",
        nargs="?",
        help="output file name for summary report\ndefault: tag-tracker.md",
        default="tag-tracker.md",
    )

    args = parser.parse_args()
    input_dir, output_name = args.input, args.output

    tracker = TagTracker(input_dir, output_name)
    tracker()
