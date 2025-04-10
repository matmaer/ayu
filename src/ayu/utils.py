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
    # tooltip_str += f"Level needed: [blue]{node_data.level_needed:>6}[/]\n"
    # tooltip_str += f"Damage: [blue]{node_data.damage:>12}[/]\n" if item.damage > 0 else ""
    # tooltip_str += (
    #     f"Attack Speed: [blue]{node_data.attack_speed:>6}[/]\n"
    #     if node_data.attack_speed > 0
    #     else ""
    # )
    # if sum([node_data.strength, item.intelligence, item.dexterity, item.luck]) > 0:
    #     tooltip_str += f"\n[yellow]{'Bonus Stats':-^20}[/]\n\n"
    #     tooltip_str += (
    #         f"Strength: [blue]{node_data.strength:>10}[/]\n" if item.strength > 0 else ""
    #     )
    #     tooltip_str += (
    #         f"Intelligence: [blue]{node_data.intelligence:>6}[/]\n"
    #         if node_data.intelligence > 0
    #         else ""
    #     )
    #     tooltip_str += (
    #         f"Dexterity: [blue]{node_data.dexterity:>9}[/]\n" if item.dexterity > 0 else ""
    #     )
    #     tooltip_str += f"Luck: [blue]{node_data.luck:>14}[/]\n" if item.luck > 0 else ""
    return tooltip_str
