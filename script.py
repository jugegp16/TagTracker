import argparse
import calendar
import json
import os
import re
from collections import defaultdict
from datetime import datetime


class bcolors:
    GREY = '\033[90m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    UNDERLINE = '\033[4m'


class TagTracker:
    def __init__(self, directory: os.path, relative_output_filepath: str) -> None:
        """
        initialize tag tracker

        Args:
            directory (os.path): search directory
            relative_output_filepath (str): output file path for report, relative or seach directory
        """

        self.dir = directory
        self.relative_output_filepath = relative_output_filepath
        self.tags = defaultdict(list)
        self.phases = [
            'to-do',
            'in-progress',
            'finished'
        ]

    def __call__(self):
        """
        analyze directory and output task report
        """

        print(f'{bcolors.OKCYAN}Analyzing...')
        self.index(self.dir, set())
        print(f'{bcolors.OKCYAN}Generating Report...')
        self.output()

    def index(self, directory: str, found_files: set):
        """
        find and index tagged files in input directory

        Args:
            directory (str): path to index
            found_files (set): searched file paths
        """

        if not os.path.isdir(directory) or '.git' in directory:
            return

        print(
            f"{bcolors.GREY}\tSearching {bcolors.UNDERLINE}{directory}{bcolors.ENDC}"
        )

        # search all files in directory
        for root, dirs, files in os.walk(directory):
            for filename in files:

                # open file and read contents
                file_path = os.path.join(root, filename)
                if file_path not in found_files:
                    found_files.add(file_path)

                    # only look at .md files
                    if '.md' not in filename:
                        continue

                    print(
                        f"{bcolors.GREY}\t\tIndexing {bcolors.UNDERLINE}{filename}{bcolors.ENDC}"
                    )

                    with open(file_path, 'r') as f:

                        # search for tags using regex
                        contents = f.read()
                        tags = re.findall(r'#\S+', contents)

                        # index tags -> filename
                        for tag in tags:
                            tag = tag[1:]

                            if '#' not in tag:
                                formatted = f"[[{file_path.split('/')[-1][:-3]}]]"
                                self.tags[tag].append(formatted)

            # recursively search subdirectories
            for subdir in dirs:
                self.index(os.path.join(directory, subdir), found_files)

    def calendar(self, cal_dir='-'):
        """
        create calendar view for current month

        Args:
            cal_dir (str, optional): directory to store daily summaries. Defaults to '-'.

        Returns:
            calendar (str): calendar string for report
        """

        res = ''
        cal = calendar.Calendar()
        today = datetime.today()

        def output_summary(f: str, key):
            dirpath = os.path.join(self.dir, cal_dir)
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath)

            filepath = os.path.join(dirpath, f'{filename}')
            with open(filepath, 'w') as output_file:
                output_file.write(
                    f'*{key}*\n\n' +
                    '\n'.join(self.tags[key]) + '\n'
                )

        # get list of tuples representing weeks in current month
        weeks = cal.monthdatescalendar(today.year, today.month)

        # generate calendar header
        for i, day in enumerate(weeks[0]):
            res += f'{day.strftime("%a")}'
            res += ' | ' if i < len(weeks[0]) - 1 else ''
        res += '\n' + '--- | ' * (len(weeks[0]) - 1) + '---\n'

        # add day numbers
        for week in weeks:
            for i, day in enumerate(week):

                # check for tasks on this day
                key = day.strftime('%Y-%m-%d')
                if self.tags.get(key):

                    # create summary file
                    filename = f'{key}.md'
                    output_summary(
                        filename,
                        key
                    )
                    # md link to summary file
                    res += ((1 - day.day // 10) * ' ')
                    res += f' [{day.day}]({cal_dir}/{filename})'

                else:
                    # add day number or empty string if day is not in current month
                    if day.month == today.month:
                        res += f'{day.day:3}'
                    else:
                        res += f'  .'

                res += ' |' if i < len(week) - 1 else ''

            res += '\n'

        return res

    def last_opened(self):
        """
        create last opened files table for obsidian users

        Returns:
            res (str): last opened files table
        """

        res = ''
        workspace_path = os.path.join(self.dir, '.obsidian/workspace.json')

        if not os.path.isfile(workspace_path):
            print(
                f"{bcolors.WARNING}\tError: No Obsidian workspace.json Detected in {workspace_path}")
            return res

        with open(workspace_path) as workspace:
            json_str = json.load(workspace)

            files = map(
                lambda i: f"[[{i.split('/')[-1]}]]",
                filter(
                    lambda filename: os.path.isfile(
                        os.path.join(self.dir, filename)
                    ),
                    json_str['lastOpenFiles']
                )
            )

            res += '\n\n\n----\n\n**Last Opened**\n- '
            res += "\n- ".join(files)

        return res

    def output(self):
        """
        write report to output file
        """

        with open(os.path.join(self.dir, self.relative_output_filepath), 'w') as output_file:

            # section line
            output_file.write('----\n')

            # calendar
            print(f"{bcolors.GREY}\tCreating Calendar")
            output_file.writelines(
                self.calendar()
            )

            # phase list
            print(f"{bcolors.GREY}\tCreating Kanban")
            for tag, file_paths in sorted(filter(
                lambda i: i[0] in self.phases,
                self.tags.items()
            ), key=lambda i: self.phases.index(i[0])):
                if not file_paths:
                    continue

                title = ' '.join(map(lambda i: i.capitalize(), tag.split('-')))
                output_file.write(
                    f'\n\n### {title}\n- ' +
                    "\n- ".join(file_paths)
                )

            # last opened files
            print(f"{bcolors.GREY}\tCreating Recently Opened")
            output_file.write(
                self.last_opened()
            )

            # tags
            print(f"{bcolors.GREY}\tCreating Tag List")
            output_file.write(
                '\n\n\n----\n*' +
                ', '.join(
                    map(
                        lambda i: f'{i[0]} ({len(i[1])})',
                        sorted(
                            filter(
                                lambda i: not bool(re.search(r'\d', str(i))),
                                self.tags.items()
                            ),
                            key=lambda i: i[1],
                        )
                    )
                ) + '*\n\n'
            )

            print(
                f"{bcolors.OKGREEN}Success!\n",
                f"\t{bcolors.GREY}Wrote Summary to {str(os.path.join(self.dir, self.relative_output_filepath))}\n"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=
        """

        ████████  █████   ██████  ████████ ██████   █████   ██████ ██   ██ ███████ ██████  
           ██    ██   ██ ██          ██    ██   ██ ██   ██ ██      ██  ██  ██      ██   ██ 
           ██    ███████ ██   ███    ██    ██████  ███████ ██      █████   █████   ██████  
           ██    ██   ██ ██    ██    ██    ██   ██ ██   ██ ██      ██  ██  ██      ██   ██ 
           ██    ██   ██  ██████     ██    ██   ██ ██   ██  ██████ ██   ██ ███████ ██   ██ 
        
                                A Markdown Task Management Tool
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-i",
        "--input",
        nargs="?",
        help="directory to search for tagged markdown files (default: current working directory)",
        default=os.getcwd()
    )
    parser.add_argument(
        "-o",
        "--output",
        nargs="?",
        help="output file path for summary report, relative to search directory (default: 'task-tracker.md' in search directory)",
        default="task-tracker.md"
    )

    args = parser.parse_args()
    input_dir, output_path = args.input, args.output

    tracker = TagTracker(input_dir, output_path)
    tracker()
