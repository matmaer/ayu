from enum import Enum
from pathlib import Path
import subprocess


class NodeType(str, Enum):
    DIR = "DIR"
    MODULE = "MODULE"
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    COROUTINE = "COROUTINE"


class EventType(str, Enum):
    COLLECTION = "COLLECTION"
    SCHEDULED = "SCHEDULED"
    OUTCOME = "OUTCOME"
    REPORT = "REPORT"


class TestOutcome(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    QUEUED = "QUEUED"


def run_test_collection():
    if Path.cwd().name == "ayu":
        command = "pytest --co".split()
    else:
        command = "uv run --with ../ayu pytest --co".split()
    subprocess.run(
        command,
        # ["pytest", "--co"],
        # ["uv", "run", "--with", "../ayu", "-U", "pytest", "--co"],
        capture_output=True,
    )


def run_all_tests(tests_to_run: list[str] | None = None):
    if Path.cwd().name == "ayu":
        command = "python -m pytest".split()
    else:
        command = "uv run --with ../ayu pytest".split()
        # command = "python -m pytest".split()

    if tests_to_run:
        command.extend(tests_to_run)

    subprocess.run(
        command,
        # ["pytest", "--co"],
        # ["uv", "run", "--with", "../ayu", "-U", "pytest", "--co"],
        capture_output=True,
    )


def get_nice_tooltip(node_data: dict) -> str | None:
    tooltip_str = ""
    # tooltip_str = f"{node_data['name'].replace("[", "\["):^20}\n"
    # tooltip_str += f"[red strike]{node_data['name'].replace('[', '\['):^20}[/]\n"
    #
    # status = node_data["status"].replace("[", "\[")
    # tooltip_str += f"\n[yellow]{status}[/]\n\n"
    return tooltip_str


def get_preview_test(file_path: str, start_line_no: int) -> str:
    with open(Path(file_path), "r") as file:
        file_lines = file.readlines()
        last_line_is_blank = False
        end_line_no = None
        for line_no, line in enumerate(file_lines[start_line_no:], start=start_line_no):
            if not line.strip():
                last_line_is_blank = True
                continue
            if (
                line.strip().startswith(("def ", "class ", "async def ", "@"))
                and last_line_is_blank
            ):
                end_line_no = line_no - 1
                break
            last_line_is_blank = False
        return "".join(file_lines[start_line_no:end_line_no]).rstrip()
