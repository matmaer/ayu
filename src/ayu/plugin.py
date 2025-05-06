import os
import asyncio
from typing import Any
import pytest
from pytest import Config, TestReport, Session, Item, Class, Function
from _pytest.terminal import TerminalReporter
from _pytest.nodes import Node

from ayu.event_dispatcher import send_event, check_connection
from ayu.classes.event import Event
from ayu.utils import EventType, TestOutcome, remove_ansi_escapes


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
        # try:
        if check_connection():
            print("connected")
            self.connected = True
        # except OSError:
        else:
            self.connected = False
            print("Websocket not connected")

    # build test tree
    def pytest_collection_finish(self, session: Session):
        if self.connected:
            print("Connected to Ayu")
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
    def pytest_runtest_logreport(self, report: TestReport):
        if self.config.pluginmanager.hasplugin("xdist") and (
            "PYTEST_XDIST_WORKER" not in os.environ
        ):
            return

        is_relevant = (report.when == "call") or (
            (report.when == "setup")
            and (report.outcome.upper() in [TestOutcome.FAILED, TestOutcome.SKIPPED])
        )

        if self.connected and is_relevant:
            asyncio.run(
                send_event(
                    event=Event(
                        event_type=EventType.OUTCOME,
                        event_payload={
                            "nodeid": report.nodeid,
                            "outcome": report.outcome.upper(),
                            "report": f"{report}",
                        },
                    )
                )
            )

    # summary after run for each tests
    @pytest.hookimpl(tryfirst=True)
    def pytest_terminal_summary(self, terminalreporter: TerminalReporter, exitstatus):
        if self.config.pluginmanager.hasplugin("xdist") and (
            "PYTEST_XDIST_WORKER" not in os.environ
        ):
            return
        report_dict = {}
        # warning report has no report.when
        for outcome, reports in terminalreporter.stats.items():
            if outcome in ["", "deselected"]:
                continue
            for report in reports:
                report_dict[report.nodeid] = {
                    "nodeid": report.nodeid,
                    # Not in warning report
                    "when": report.when,
                    "caplog": report.caplog,
                    "longreprtext": remove_ansi_escapes(report.longreprtext),
                    "duration": report.duration,
                    "outcome": report.outcome,
                    "lineno": report.location[1],
                    "otherloc": report.location[2],
                }

        # import json

        if self.connected:
            asyncio.run(
                send_event(
                    event=Event(
                        event_type=EventType.REPORT,
                        event_payload={
                            "report": report_dict,
                        },
                    )
                )
            )


def build_dict_tree(items: list[Item]) -> dict:
    markers = set()

    def create_node(
        node: Node, parent_name: Node | None = None, parent_type: Node | None = None
    ) -> dict[Any, Any]:
        markers.update([mark.name for mark in node.own_markers])

        return {
            "name": node.name,
            "nodeid": node.nodeid,
            "markers": [mark.name for mark in node.own_markers],
            "path": node.path.as_posix(),
            "lineno": node.reportinfo()[1]
            if isinstance(node, Class)
            else (node.location[1] if isinstance(node, Function) else 0),
            "parent_name": parent_name,
            "parent_type": parent_type,
            "type": type(node).__name__.upper(),
            "favourite": False,
            "status": "",
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

    return {"tree": tree, "meta": {"test_count": len(items), "markers": list(markers)}}
