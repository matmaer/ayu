import os
import shutil
import re
from enum import Enum
from pathlib import Path
import subprocess

from ayu.constants import WEB_SOCKET_PORT, WEB_SOCKET_HOST


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
    # handle those
    XFAILED = "XFAILED"
    XPASSED = "XPASSED"
    ERROR = "XPASSED"


def run_test_collection(tests_path: str | None = None):
    """Collect All Tests without running them"""
    if not ayu_is_run_as_tool():
        command = "uv run pytest --co".split()
    else:
        command = "uv run --with ayu pytest --co".split()

    if tests_path:
        command.extend([tests_path])

    subprocess.run(
        command,
        capture_output=True,
    )


def run_all_tests(tests_path: str | None = None, tests_to_run: list[str] | None = None):
    """Run all selected tests"""
    if not ayu_is_run_as_tool():
        command = "uv run python -m pytest".split()
    else:
        command = "uv run --with ayu pytest".split()
        # command = "python -m pytest".split()

    if tests_to_run:
        command.extend(tests_to_run)
    else:
        if tests_path:
            command.extend([tests_path])

    subprocess.run(
        command,
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
    """Read the test file from nodeid and use the linenumber
    and some rules to display the test function"""
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


def get_ayu_websocket_host_port() -> tuple[str, int]:
    host: str = os.environ.get("AYU_HOST", WEB_SOCKET_HOST)
    port: int = int(os.environ.get("AYU_PORT", WEB_SOCKET_PORT))
    return host, port


def remove_ansi_escapes(string_to_remove: str) -> str:
    """Remove ansi escaped strings from colored pytest output"""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", string_to_remove)


def uv_is_installed():
    if shutil.which("uv"):
        return True
    return False


def project_is_uv_managed():
    toml_path = Path.cwd() / "pyproject.toml"
    return toml_path.exists()


def ayu_is_run_as_tool():
    result = subprocess.run(
        "uv tree --package ayu".split(), capture_output=True, text=True
    )
    if result.stdout:
        return False
    return True
