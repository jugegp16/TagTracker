# TagTracker: A Markdown Task Management Tool
Efficiently track and organize tagged markdown files.

## How to Use
```shell
usage: tag-tracker.py [-h] [-i [INPUT]] [-o [OUTPUT]]

        ████████  █████   ██████  ████████ ██████   █████   ██████ ██   ██ ███████ ██████
           ██    ██   ██ ██          ██    ██   ██ ██   ██ ██      ██  ██  ██      ██   ██
           ██    ███████ ██   ███    ██    ██████  ███████ ██      █████   █████   ██████
           ██    ██   ██ ██    ██    ██    ██   ██ ██   ██ ██      ██  ██  ██      ██   ██
           ██    ██   ██  ██████     ██    ██   ██ ██   ██  ██████ ██   ██ ███████ ██   ██

                                A Markdown Task Management Tool


optional arguments:
  -h, --help            show this help message and exit
  -i [INPUT], --input [INPUT]
                        directory to search for tagged markdown files
                        default: current working directory
  -o [OUTPUT], --output [OUTPUT]
                        output file path for summary report
                        default: ./tag-tracker.md
```
## Recommended Setup
### Markdown Users
- Create a hotkey on your system or favorite note editor
- Set up an alias in your shell setup file
    - `alias task='Python3 /path/tag-tracker.py -i /path/to/notes -o /path/to/notes/tag-tracker.md'`

### Obsidian Users
1. Download [obsidian-shellcommands](https://github.com/Taitava/obsidian-shellcommands) community plugin
2. Enter new shell command
    - `Python3 /path/tag-tracker.py -i /path/to/notes -o /path/to/notes/tag-tracker.md`
3. Go to hotkey settings and create a shortcut (e.g cmd + o)

## Features
- Monthly calendar view
- Kanban-style task board
- Recently opened files
- Tagged file list

## Requirements
- Python 3.x
