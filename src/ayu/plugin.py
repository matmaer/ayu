import asyncio
from typing import Any
import pytest
from pytest import Config, TestReport, Session, Item
from _pytest.terminal import TerminalReporter
from _pytest.nodes import Node

from ayu.event_dispatcher import send_event, check_connection
from ayu.classes.event import Event
from ayu.utils import EventType


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--disable-ayu",
        "--da",
        action="store_true",
        default=False,
        help="Enable Ayu plugin functionality",
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    if not config.getoption("--disable-ayu"):
        config.pluginmanager.register(Ayu(config), "ayu_plugin")


class Ayu:
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
        print("Connected to Ayu")
        if self.connected:
            if session.config.getoption("--collect-only"):
                tree = build_dict_tree(items=session.items)
                asyncio.run(
                    send_event(
                        event=Event(
                            event_type=EventType.COLLECTION,
                            event_payload=tree,
                        )
                    )
                )
            else:
                asyncio.run(
                    send_event(
                        event=Event(
                            event_type=EventType.SCHEDULED,
                            event_payload=[item.nodeid for item in session.items],
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

    # summary after run for each tests
    @pytest.hookimpl(tryfirst=True)
    def pytest_terminal_summary(self, terminalreporter: TerminalReporter):
        if self.connected:
            asyncio.run(
                send_event(
                    event=Event(
                        event_type=EventType.REPORT,
                        event_payload={
                            "report": f"{terminalreporter.stats.get('', [])}",
                        },
                    )
                )
            )
        return
        for report in terminalreporter.stats.get("", []):
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


def build_dict_tree(items: list[Item]) -> dict:
    def create_node(
        node: Node, parent_name: Node | None = None, parent_type: Node | None = None
    ) -> dict[Any, Any]:
        return {
            "name": node.name,
            "nodeid": node.nodeid,
            "markers": [mark.name for mark in node.own_markers],
            "path": node.path.as_posix(),
            "parent_name": parent_name,
            "parent_type": parent_type,
            "type": type(node).__name__.upper(),
            "children": [],
        }

    def add_node(node_list: list[Node], sub_tree: dict):
        if not node_list:
            return

        # take root node
        current_node = node_list.pop(0)
        node_dict = create_node(
            node=current_node,
            parent_name=current_node.parent.name,
            parent_type=type(current_node.parent).__name__.upper(),
        )

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

    return {"tree": tree, "meta": {"test_count": len(items)}}
