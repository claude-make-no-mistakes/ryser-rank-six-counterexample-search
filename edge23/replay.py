"""Replay the exact 23-edge proof in a temporary directory."""

from pathlib import Path
from shutil import copyfile
from subprocess import run
from sys import executable
from tempfile import TemporaryDirectory


def main():
    sources = Path(__file__).resolve().parent
    stages = (
        ("node", "scout-frontier.js"),
        (executable, "-E", "-B", "verify-pairs-exact.py"),
        (executable, "-E", "-B", "certify-rows.py", "--check"),
        (executable, "-E", "-B", "check-final.py"),
    )
    with TemporaryDirectory(prefix="ryser-edge23-") as directory:
        for file in ("scout-frontier.js", "verify-pairs-exact.py", "certify-rows.py",
                     "row-duals.json", "check-final.py"):
            copyfile(sources / file, Path(directory) / file)
        for command in stages:
            run(command, cwd=directory, check=True)
    print("All 23-edge systems excluded")


if __name__ == "__main__":
    main()
