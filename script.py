# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests",
#     "rich",
# ]
# ///

# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

# import rich
import sys
from rich import print
import requests
# import pygame


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    print(sys.version)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/


# Working with a single script file:
#
# Commands for adding dependencies:
# uv init --script script.py --python 3.8
# uv add --script script.py "rich"
# uv add --script script.py "requests"
# uv run script.py
#
# Command for using a dependency everytime we are running the script:
# uv run --with rich --python 3.8 script.py
# uv run --with rich --with requests --python 3.8 script.py
#
# General commands:
# uv python find 3.9
# uv run --python 3.9 script.py
# uv run script.py
# arch
# uname -m
# uv python install 3.8
# uv python list
# pip install uv
#
#
#
# Working with a python Project (Not just a script)
# uv init --> terminal output: Initialized project `langgraph-tutorial`
# uv run python script.py
#
#
# To add dependencies manually:
# manually add them into dependencies = [] in pyproject.toml
# and then command: uv sync or  uv sync --reinstall
#
#
# Note: I tried to add and import pygame. To run this with uv:
#   uv run python script.py   # works reliably, we are explicitly calling the project .venv python
#   uv run script.py          # only works if file has a shebang (#!/usr/bin/env python3), might not use the right python interpreter
# Or activate the venv:
#   source .venv/bin/activate && command:  python script.py
#
#
# Making a new lock file command: uv lock
# Removing dependencies: uv remove
# Dependency removal with uv:
# - If listed in pyproject.toml → uv remove <pkg> && uv sync
# - If only stuck in lock → uv lock --recreate && uv sync --reinstall
#


# If you want to e able to use pip commands as you normally would use the command: uv pip

