import argparse
import calendar
import logging
import os
import re
from collections import defaultdict
from datetime import datetime
import utils


class bcolors:
    GREY = "\033[90m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    ENDC = "\033[0m"
    UNDERLINE = "\033[4m"


class TagTracker:
    def __init__(self, directory: str, output_name: str) -> None:
        self.dir = directory
        self.output_name = output_name
        self.tags = defaultdict(list)
        self.phases = ["to-do", "in-progress", "finished"]
        self.settings = utils.get_settings()

    def __call__(self):
        logging.info(f"{bcolors.OKCYAN}Analyzing...")
        self.index(self.dir, set())
        logging.info(f"{bcolors.OKCYAN}Generating Report...")
        self.output()

    def index(self, directory: str, found_files: set):
        """find and index tagged files in input directory"""
        if not os.path.isdir(directory) or ".git" in directory:
            return

        logging.info(
            f"{bcolors.GREY}\tSearching {bcolors.UNDERLINE}{directory}{bcolors.ENDC}"
        )

        # search all files in directory
        for root, dirs, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                if file_path in found_files or filename[-3:] != ".md":
                    continue

                logging.info(
                    f"{bcolors.GREY}\t\tIndexing {bcolors.UNDERLINE}{filename}{bcolors.ENDC}"
                )

                found_files.add(file_path)
                with open(file_path, "r") as f:
                    contents = f.read()

                tags = re.findall(r"#\S+", contents)
                cleaned_tags = [x[1:] for x in tags if "##" not in x]

                for tag in cleaned_tags:
                    rel_path: str = os.path.relpath(file_path, self.dir)
                    formatted = "[{}]({})".format(
                        file_path.split("/")[-1][:-3], rel_path.replace(" ", "%20")
                    )
                    self.tags[tag].append(formatted)

            # search subdirectories recursively
            for subdir in dirs:
                self.index(os.path.join(directory, subdir), found_files)

    def calendar(self, cal_dir="-"):
        """create calendar view for current month"""
        res = ""
        cal = calendar.Calendar()
        today = datetime.today()
        emdbed_str = "!" if self.settings["embedPagesInDailyView"] else ""
        cal_dir = (
            self.settings["calendarDirectory"]
            if self.settings["calendarDirectory"]
            else cal_dir
        )

        def output_summary(key):
            dirpath = os.path.join(self.dir, cal_dir)
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath)

            content = "*{0}*\n\n{1}{2}".format(
                key, emdbed_str, f"\n{emdbed_str}".join(self.tags[key])
            )
            filepath = os.path.join(dirpath, f"{key}.md")
            with open(filepath, "w") as output_file:
                output_file.write(content)

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
                        res += "  ."

                res += " |" if i < len(week) - 1 else ""

            res += "\n"

        return res

    def last_opened(self):
        """create last opened files table for obsidian users"""
        workspace_json = utils.get_workspace(self.dir)
        if not workspace_json:
            logging.warning(
                f"{bcolors.WARNING}\tError: No Obsidian workspace.json Detected"
            )
            return ""

        files = map(
            lambda i: f"[{i.split('/')[-1]}]({i.replace(' ', '%20')})",
            filter(
                lambda filename: os.path.isfile(os.path.join(self.dir, filename)),
                workspace_json["lastOpenFiles"],
            ),
        )

        return "\n\n\n----\n\n**Last Opened**\n- " + "\n- ".join(files)

    def kan_ban(self):
        """create kan ban board"""
        max_files = (
            self.settings["maxFilesShown"] if "maxFilesShown" in self.settings else 10
        )
        res = ""
        for tag, file_paths in sorted(
            filter(lambda i: i[0] in self.phases, self.tags.items()),
            key=lambda i: self.phases.index(i[0]),
        ):
            if not file_paths:
                continue

            title = " ".join(map(lambda i: i.capitalize(), tag.split("-")))
            res += f"\n\n### {title}\n- " + "\n- ".join(file_paths[:max_files])

        return res

    def tag_list(self):
        cleaned_tags = map(
            lambda i: f"{i[0]} ({len(i[1])})",
            sorted(
                filter(
                    lambda i: not bool(re.search(r"\d{4}-\d{2}-\d{2}", i[0])),
                    self.tags.items(),
                ),
                key=lambda i: len(i[1]),
                reverse=True,
            ),
        )
        return f"\n\n\n----\n*{', '.join(cleaned_tags)}*\n\n"

    def output(self):
        """write report to output file"""
        with open(os.path.join(self.dir, self.output_name), "w") as output_file:
            output_file.write("----\n")

            logging.info(f"{bcolors.GREY}\tCreating Calendar")
            output_file.writelines(self.calendar())

            logging.info(f"{bcolors.GREY}\tCreating Kanban")
            output_file.write(self.kan_ban())

            logging.info(f"{bcolors.GREY}\tCreating Recently Opened")
            output_file.write(self.last_opened())

            logging.info(f"{bcolors.GREY}\tCreating Tag List")
            output_file.write(self.tag_list())

        logging.info(
            f"{bcolors.OKGREEN}Success!\n\t{bcolors.GREY}Wrote summary to\n"
            + os.path.join(self.dir, self.output_name),
        )

        print(f"Updated {self.output_name}")


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
    parser.add_argument(
        "-log",
        "--loglevel",
        default="warning",
        help="Provide logging level. Example --loglevel debug, default=warning",
    )

    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel.upper())
    input_dir, output_name = args.input, args.output

    tracker = TagTracker(input_dir, output_name)
    tracker()
