from typing import Any
import os
import shutil
import re
from enum import Enum
from pathlib import Path
import subprocess

import asyncio
from pytest import Item, Class, Function
from _pytest.nodes import Node

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
    COVERAGE = "COVERAGE"
    DEBUG = "DEBUG"


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
    if ayu_is_run_as_tool():
        command = "uv run --with ayu pytest --co".split()
    else:
        command = "uv run pytest --co".split()

    if tests_path:
        command.extend([tests_path])

    return subprocess.run(
        command,
        capture_output=True,
    )


async def run_all_tests(
    tests_path: str | None = None, tests_to_run: list[str] | None = None
):
    """Run all selected tests"""
    if ayu_is_run_as_tool():
        command = "uv run --with ayu pytest "
    else:
        command = "uv run python -m pytest "

    if tests_to_run:
        command += " ".join(tests_to_run)
    else:
        if tests_path:
            command += tests_path
    return await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
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


def build_dict_tree(items: list[Item]) -> dict:
    markers = set()

    def create_node(node: Node) -> dict[Any, Any]:
        markers.update([mark.name for mark in node.own_markers])
        return test_node_to_dict(node=node)

    def add_node(node_list: list[Node], sub_tree: dict):
        if not node_list:
            return

        # take root node
        current_node = node_list.pop(0)
        node_dict = create_node(node=current_node)

        existing_node = next(
            (
                node
                for node in sub_tree["children"]
                if node["nodeid"] == current_node.nodeid
            ),
            None,
        )

        if existing_node is None:
            sub_tree["children"].append(node_dict)
            existing_node = node_dict

        add_node(
            node_list=node_list,
            sub_tree=existing_node,
        )

    tree: dict[Any, Any] = {}
    root = items[0].listchain()[1]
    tree[root.name] = create_node(node=root)

    for item in items:
        # gets all parents except session
        parts_to_collect = item.listchain()[1:]
        add_node(node_list=parts_to_collect[1:], sub_tree=tree[root.name])

    return {"tree": tree, "meta": {"test_count": len(items), "markers": list(markers)}}


def coverage_str_to_dict(coverage_report_str: str) -> dict[str, dict]:
    report_dict: dict[str, dict] = {}
    lines = coverage_report_str.strip().split("\n")
    for line in lines[5:-2]:
        parts = line.split()

        raw_lines_missing = [line_part.replace(",", "") for line_part in parts[4:]]
        int_lines_missing = []
        for line_range in raw_lines_missing:
            int_lines = [int(line) for line in line_range.split("-")]
            int_lines_missing.append(int_lines)

        module_name = parts[0]
        n_statements = int(parts[1])
        n_missed = int(parts[2])
        percent_covered = parts[3]

        report_dict[module_name] = {}
        report_dict[module_name]["n_statements"] = n_statements
        report_dict[module_name]["n_missed"] = n_missed
        report_dict[module_name]["percent_covered"] = percent_covered
        report_dict[module_name]["lines_missing"] = int_lines_missing

    return report_dict


def get_coverage_data(coverage_file=".coverage"):
    import coverage

    cov = coverage.Coverage(data_file=coverage_file)
    cov.load()

    report_dict = {}

    for file_path in cov.get_data().measured_files():
        file_data = cov.analysis2(file_path)
        # analysis2 returns: (0:filename, 1:statements, 2:excluded, 3:missing, 4:partial)
        total_statements = len(file_data[1])  # All statements
        missing_statements = len(file_data[3])  # Uncovered statements
        coverage_percent = (
            (total_statements - missing_statements) / total_statements * 100
            if total_statements > 0
            else 0
        )

        # Store data for this file
        report_dict[Path(file_path).relative_to(Path.cwd()).as_posix()] = {
            "n_statements": total_statements,
            "n_missed": missing_statements,
            "percent_covered": round(coverage_percent, 2),
            "lines_missing": file_data[3],  # List of uncovered line numbers
        }

    return report_dict


def test_node_to_dict(node: Node) -> dict[str, Any]:
    return {
        "name": node.name,
        "nodeid": node.nodeid,
        "markers": [mark.name for mark in node.own_markers],
        "path": node.path.as_posix(),
        "lineno": node.reportinfo()[1]
        if isinstance(node, Class)
        else (node.location[1] if isinstance(node, Function) else 0),
        "parent_name": node.parent.name if node.parent else None,
        "parent_type": type(node.parent).__name__.upper() if node.parent else None,
        "type": type(node).__name__.upper(),
        "favourite": False,
        "status": "",
        "children": [],
    }
