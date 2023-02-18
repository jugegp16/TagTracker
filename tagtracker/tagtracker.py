import argparse
import json
import os
import re
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Tuple

from setup import bcolors, view_options, View, Workspace
from views import *


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
        self.tags: DefaultDict[str, List[str]] = defaultdict(list)
        self.reports: DefaultDict[str, List[Tuple[View, Any]]] = None
        self.settings: Dict = None

    def __call__(self):
        """
        analyze directory and output task report
        """

        self.__parse_settings()
        self.__parse_config()

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

    def __parse_config(self):
        config = {}

        path = os.path.join(os.path.split(os.path.dirname(__file__))[0], "config.json")
        if os.path.isfile(path):
            with open(path) as config:
                config = json.load(config)

        reports = defaultdict(list)  # path -> views to render

        for output_path, all_views in config.items():
            print(output_path)

            for view_name, options in all_views.items():
                print("\t", view_name, options)

                report, fstr, pstr = None, None, None

                # todo - pass in arbitrary options for devs to use

                # load correct view given name
                report = view_options[view_name]

                if options:
                    fstr = options["filter"] if "filter" in options else None
                    pstr = options["path"] if "path" in options else None

                if report:
                    reports[pstr if pstr else output_path].append(
                        (report, fstr if fstr else None, options if options else None)
                    )

        self.reports = reports

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

    def output(self):
        """
        write report to output file
        """

        # todo change this to state
        workspace: Workspace = Workspace()
        workspace.path = self.dir
        workspace.settings = self.settings
        workspace.tags = self.tags

        for output_name, funcs in self.reports.items():
            with open(os.path.join(self.dir, output_name + ".md"), "w") as output_file:
                # section line
                output_file.write("----\n")

                for func, _filter, options in funcs:
                    # to do: aplly filter on tag name
                    if _filter:
                        workspace.tags = filter(
                            lambda i: bool(re.search(_filter), i),
                            self.tags.items(),
                        )

                    workspace.options = options

                    output_file.write(func(workspace))

                print(
                    f"{bcolors.OKGREEN}Success!\n",
                    f"\t{bcolors.GREY}Wrote Summary to {os.path.join(self.dir, output_name)}.md\n",
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
    parser.add_argument(
        "-c",
        "--config",
        nargs="?",
        help="config file with report structure\ndefault: config.json",
        default="config.json",
    )

    args = parser.parse_args()
    input_dir, output_name = args.input, args.output

    tracker = TagTracker(input_dir, output_name)
    tracker()

# for i in view_options:
#     print(i, view_options[i])
