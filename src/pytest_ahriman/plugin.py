import pytest
from pytest import Config, TestReport, Session, Item
from _pytest.terminal import TerminalReporter
from _pytest.nodes import Node

from pprint import pprint


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--disable-ahriman",
        "--da",
        action="store_true",
        default=False,
        help="Enable Orisa plugin functionality",
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    if not config.getoption("--disable-ahriman"):
        config.pluginmanager.register(Ahriman(config), "ahriman_plugin")


class Ahriman:
    def __init__(self, config: Config):
        self.config = config

    def pytest_collection_modifyitems(
        self, session: Session, config: Config, items: TestReport
    ):
        return
        for item in items:
            print(f"item: {item}")

    def pytest_collection_finish(self, session: Session):
        build_tree(items=session.items)
        return

        for item in session.items:
            print()
            print(f"list: {item.listchain()[1:]}")
            print(f"item_node: {item.nodeid}")
            print(f"item: {item}")

    # Infos during run
    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_logreport(self, report: TestReport):
        if report.when == "call":  # After test execution
            print(f"duration: {report.duration:.3f}")
            print(f"nodeid: {report.nodeid}")
            print(f"dir:{report.location[0]}")
            print(f"line_no:{report.location[1]}")
            print(f"test:{report.location[2]}")
            print(f"{report.outcome}")

    # Infos during run
    @pytest.hookimpl(tryfirst=True)
    def pytest_terminal_summary(self, terminalreporter: TerminalReporter):
        return
        for report in terminalreporter.stats[""]:
            if report.when == "call":
                return
            print("## Summary ##")
            print(f"when: {report.when}")
            print(f"cap: {report.caplog}")
            print(f"long: {report.longreprtext}")
            print(f"dur: {report.duration}")
            print(f"outcome: {report.outcome}")
            print(f"err: {report.capstderr}")
            print("## End ##")


def build_tree(items: list[Item]):
    def create_node(
        node: Node, parent_name: Node | None = None, parent_type: Node | None = None
    ) -> dict:
        return {
            "name": node.name,
            "id": node.nodeid,
            "path": node.path,
            "parent_name": parent_name,
            "parent_type": parent_type,
            "type": type(node).__name__.upper(),
            "children": [],
        }

    def add_node(node_list: list[Node], tree: dict):
        if not node_list:
            return

        node = node_list.pop(0)
        data = create_node(
            node=node,
            parent_type=type(node.parent).__name__.upper(),
            parent_name=node.parent.name,
        )

        if "children" not in tree:
            tree["children"] = []

        existing_node = next(
            (child for child in tree["children"] if child["name"] == data["name"]), None
        )

        if existing_node is None:
            tree["children"].append(data)
            existing_node = data

        add_node(node_list=node_list, tree=existing_node)

    tree = {}

    for item in items:
        parts_to_collect = item.listchain()[1:]
        if parts_to_collect:
            root = parts_to_collect[0]

            if root.name not in tree:
                tree[root.name] = create_node(root)
            add_node(parts_to_collect[1:], tree[root.name])

    pprint(tree, sort_dicts=False)
    return tree
