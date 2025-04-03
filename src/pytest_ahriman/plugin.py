import asyncio
import pytest
from pytest import Config, TestReport, Session, Item
from _pytest.terminal import TerminalReporter
from _pytest.nodes import Node

from pytest_ahriman.event_dispatcher import send_event, check_connection


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
        self.connected = False
        try:
            asyncio.run(check_connection())
            print("connected")
            self.connected = True
        except OSError:
            self.connected = False
            print("Websocket not connected")

    # build test tree
    def pytest_collection_finish(self, session: Session):
        if self.connected:
            tree = build_tree(items=session.items)
            asyncio.run(send_event(msg=f"{tree}"))
        return

    # gather status updates during run
    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_logreport(self, report: TestReport):
        if report.when == "call":  # After test execution
            if self.connected:
                asyncio.run(
                    send_event(msg=f"report: {report.nodeid}: {report.outcome}")
                )
            # print(f"duration: {report.duration:.3f}")
            # print(f"nodeid: {report.nodeid}")
            # print(f"dir:{report.location[0]}")
            # print(f"line_no:{report.location[1]}")
            # print(f"test:{report.location[2]}")
            # print(f"{report.outcome}")

    # summary after run for each tests
    @pytest.hookimpl(tryfirst=True)
    def pytest_terminal_summary(self, terminalreporter: TerminalReporter):
        for report in terminalreporter.stats[""]:
            if report.when == "teardown":
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

    return tree
