import argparse
import calendar
import logging
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
import utils

DESCRIPTION = """

    ████████  █████   ██████  ████████ ██████   █████   ██████ ██   ██ ███████ ██████  
        ██    ██   ██ ██          ██    ██   ██ ██   ██ ██      ██  ██  ██      ██   ██ 
        ██    ███████ ██   ███    ██    ██████  ███████ ██      █████   █████   ██████  
        ██    ██   ██ ██    ██    ██    ██   ██ ██   ██ ██      ██  ██  ██      ██   ██ 
        ██    ██   ██  ██████     ██    ██   ██ ██   ██  ██████ ██   ██ ███████ ██   ██ 

                            A Markdown Task Management Tool

    Example Usage:
        Python3 tag-tracker.py -i ~/Documents/notes/ -o Readme.md -m 2
"""

DEFAULT_TAGS = ["to-do", "in-progress", "finished"]


class bcolors:
    GREY = "\033[90m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    ENDC = "\033[0m"
    UNDERLINE = "\033[4m"


class TagTracker:
    def __init__(self, args):
        self.dir = args.input
        self.output_name = args.output
        self.num_months = args.months
        self.input_tags = args.tags
        self.tag_filter = set(args.filter)
        self.disable_calendar = args.disable_calendar
        self.disable_recently_opened = args.disable_recently_opened
        self.tagged_files = defaultdict(list)
        self.file_tags = defaultdict(set)
        self.settings = utils.get_settings()

    def __call__(self):
        logging.info(f"{bcolors.OKCYAN}Analyzing...")
        self.index(self.dir, set())
        if self.tag_filter:
            self.apply_filter()
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
                found_files.add(file_path)

                logging.info(
                    f"{bcolors.GREY}\t\tIndexing {bcolors.UNDERLINE}{filename}{bcolors.ENDC}"
                )

                # create markdown path
                rel_path = os.path.relpath(file_path, self.dir)
                formatted_path = "[{}]({})".format(
                    file_path.split("/")[-1][:-3], rel_path.replace(" ", "%20")
                )

                with open(file_path, "r") as f:
                    contents = f.read()

                tags = re.findall(r"#\S+", contents)
                cleaned_tags = [x[1:] for x in tags if "##" not in x]
                for tag in cleaned_tags:
                    self.tagged_files[tag].append(formatted_path)

                self.file_tags[formatted_path] = set(cleaned_tags)

            # search subdirectories recursively
            for subdir in dirs:
                self.index(os.path.join(directory, subdir), found_files)

    def apply_filter(self):
        filtered_tagged_files = {}
        for tag, files in self.tagged_files.items():
            if (
                not re.match("^[0-9]{4}\-[0-9]{2}\-[0-9]{2}$", tag)
                and tag not in self.tag_filter
            ):
                continue

            filtered_files = []
            for file in files:
                # if the tag is a date, check whether it contains a tag in the filter
                if tag not in self.tag_filter and not self.tag_filter.intersection(
                    self.file_tags[file]
                ):
                    continue
                filtered_files.append(file)

            filtered_tagged_files[tag] = filtered_files
        self.tagged_files = filtered_tagged_files

    def calendar(self, as_of_date: datetime.date, cal_dir="-"):
        """create calendar view for current month"""

        def output_summary(key):
            dirpath = os.path.join(self.dir, cal_dir)
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath)

            content = "*{0}*\n\n{1}{2}".format(
                key, emdbed_str, f"\n{emdbed_str}".join(self.tagged_files[key])
            )
            filepath = os.path.join(dirpath, f"{key}.md")
            with open(filepath, "w") as output_file:
                output_file.write(content)

        res = ""
        cal = calendar.Calendar()
        emdbed_str = "!" if self.settings["embedPagesInDailyView"] else ""
        cal_dir = (
            self.settings["calendarDirectory"]
            if self.settings["calendarDirectory"]
            else cal_dir
        )
        # get list of tuples representing weeks in current month
        weeks = cal.monthdatescalendar(as_of_date.year, as_of_date.month)

        # generate calendar header
        res += f"**{as_of_date.strftime('%B')} {as_of_date.year}**" + "\n\n"
        for i, day in enumerate(weeks[0]):
            res += f'{day.strftime("%a")}'
            res += " | " if i < len(weeks[0]) - 1 else ""
        res += "\n" + "--- | " * (len(weeks[0]) - 1) + "---\n"

        # add day numbers
        for week in weeks:
            for i, day in enumerate(week):
                # check for tasks on this day
                key = day.strftime("%Y-%m-%d")
                if self.tagged_files.get(key):
                    # create summary file
                    output_summary(key)
                    filename = f"{key}.md"
                    # create a markdown link to the summary file
                    res += " " * (1 - day.day // 10)
                    res += f" [{day.day}]({cal_dir}/{filename})"
                else:
                    # add day number if in current month
                    if day.month == as_of_date.month:
                        res += f"{day.day:3}"
                    else:
                        res += "  ."
                res += " |" if i < len(week) - 1 else ""
            res += "\n"
        return res + "\n"

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

        return "----\n\n**Last Opened**\n- " + "\n- ".join(files)

    def tag_board(self):
        """create tag board"""
        max_files = (
            self.settings["maxFilesShown"] if "maxFilesShown" in self.settings else 10
        )
        res = ""
        for tag, file_paths in sorted(
            filter(lambda i: i[0] in self.input_tags, self.tagged_files.items()),
            key=lambda i: self.input_tags.index(i[0]),
        ):
            if not file_paths:
                continue

            title = " ".join(map(lambda i: i.capitalize(), tag.split("-")))
            res += f"\n\n**{title}**\n- " + "\n- ".join(file_paths[:max_files])

        return res

    def output(self):
        """write report to output file"""
        with open(os.path.join(self.dir, self.output_name), "w") as output_file:
            if not self.disable_calendar:
                logging.info(f"{bcolors.GREY}\tCreating Calendar")
                for i in range(self.num_months, 0, -1):
                    delta = timedelta(weeks=(i - 1) * 4)
                    output_file.write(self.calendar(datetime.today() - delta))

            tag_board = self.tag_board()
            if tag_board:
                logging.info(f"{bcolors.GREY}\tCreating Tag Board")
                output_file.write("\n---" + tag_board + "\n\n")

            if not self.disable_recently_opened:
                logging.info(f"{bcolors.GREY}\tCreating Recently Opened")
                output_file.write(self.last_opened())

        logging.info(
            f"{bcolors.OKGREEN}Success!\n\t{bcolors.GREY}Wrote summary to\n"
            + os.path.join(self.dir, self.output_name),
        )

        print(f"Updated {self.output_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        nargs="?",
        help="directory to search for tagged markdown files, default='.'",
        default=os.getcwd(),
    )
    parser.add_argument(
        "-o",
        "--output",
        nargs="?",
        help="output file name for summary report, default='tag-tracker.md'",
        default="tag-tracker.md",
    )
    parser.add_argument(
        "-log",
        "--loglevel",
        default="warning",
        help="provide logging level. Example --loglevel debug, default=warning",
    )
    parser.add_argument(
        "-m",
        "--months",
        default=1,
        type=int,
        help="number of months generated in the calendar report, default=1",
    )
    parser.add_argument(
        "-t",
        "--tags",
        default=DEFAULT_TAGS,
        nargs="+",
        help=f"tags used to generate tag list, default={DEFAULT_TAGS}",
    )
    parser.add_argument(
        "-f",
        "--filter",
        default=[],
        nargs="+",
        help="tags to use for the report, defaults to all",
    )
    parser.add_argument("--disable-calendar", action="store_true")
    parser.add_argument("--disable-recently-opened", action="store_true")

    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel.upper())
    tracker = TagTracker(args)
    tracker()
