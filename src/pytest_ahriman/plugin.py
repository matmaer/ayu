import asyncio
import pytest
from pytest import Config, TestReport, Session, Item
from _pytest.terminal import TerminalReporter
from _pytest.nodes import Node

from pytest_ahriman.event_dispatcher import send_event, check_connection
from pytest_ahriman.classes.event import Event
from pytest_ahriman.utils import EventType


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
            asyncio.run(
                send_event(
                    event=Event(
                        event_type=EventType.COLLECTION,
                        event_payload=tree,
                    )
                )
            )
        return

    # gather status updates during run
    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report: TestReport):
        is_relevant = (report.when == "call") or (
            (report.when == "setup") and (report.outcome in ["failed", "skipped"])
        )

        if self.connected and is_relevant:
            asyncio.run(
                send_event(
                    event=Event(
                        event_type=EventType.OUTCOME,
                        event_payload={
                            "nodeid": report.nodeid,
                            "outcome": report.outcome,
                        },
                    )
                )
            )
            # asyncio.run(
            #     send_event(msg=f"report: {report.when} {report.nodeid} {report.outcome}")
            # )

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
                print(f"line_no:{report.location[1]}")
                print(f"test:{report.location[2]}")
                print("## End ##")


def build_tree(items: list[Item]):
    def create_node(
        node: Node, parent_name: Node | None = None, parent_type: Node | None = None
    ) -> dict:
        return {
            "name": node.name,
            "id": node.nodeid,
            "path": node.path.as_posix(),
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
