# TagTracker: A Markdown Task Management Tool
Efficiently track and organize tagged markdown files.

### How to Use
```shell
usage: script.py [-h] [-i [INPUT]] [-o [OUTPUT]]

        ████████  █████   ██████  ████████ ██████   █████   ██████ ██   ██ ███████ ██████
           ██    ██   ██ ██          ██    ██   ██ ██   ██ ██      ██  ██  ██      ██   ██
           ██    ███████ ██   ███    ██    ██████  ███████ ██      █████   █████   ██████
           ██    ██   ██ ██    ██    ██    ██   ██ ██   ██ ██      ██  ██  ██      ██   ██
           ██    ██   ██  ██████     ██    ██   ██ ██   ██  ██████ ██   ██ ███████ ██   ██

                                A Markdown Task Management Tool


optional arguments:
  -h, --help            show this help message and exit
  -i [INPUT], --input [INPUT]
                        directory to search for tagged markdown files (default: current working directory)
  -o [OUTPUT], --output [OUTPUT]
                        output file path for summary report, relative to search directory (default: 'task-tracker.md' in search directory)
```
> Tip: Set up an alias/cron job to streamline your workflow further!

### Features
- Monthly calendar view
- Kanban-style task board
- Recently opened files
- Tagged file list

### Requirements
- Python 3.x
