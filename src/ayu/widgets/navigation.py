from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ayu.app import AyuApp
from textual import work
from textual.reactive import reactive
from textual.binding import Binding
from textual.widgets import Tree
from textual.widgets.tree import TreeNode
from rich.text import Text

from ayu.utils import EventType, get_nice_tooltip
from ayu.constants import OUTCOME_SYMBOLS


class TestTree(Tree):
    app: "AyuApp"
    BINDINGS = [
        Binding("r", "collect_tests", "Refresh"),
        Binding("j,down", "cursor_down"),
        Binding("k,up", "cursor_up"),
        Binding("f", "mark_test", "⭐ Mark"),
    ]
    show_root = False
    auto_expand = True
    guide_depth = 2

    count_queue: reactive[int] = reactive(0)
    count_passed: reactive[int] = reactive(0)
    count_failed: reactive[int] = reactive(0)
    count_skipped: reactive[int] = reactive(0)

    def on_mount(self):
        self.app.dispatcher.register_handler(
            event_type=EventType.COLLECTION,
            handler=lambda data: self.build_tree(data),
        )
        self.app.dispatcher.register_handler(
            event_type=EventType.SCHEDULED,
            handler=lambda data: self.mark_tests_as_running(data),
        )
        self.app.dispatcher.register_handler(
            event_type=EventType.OUTCOME,
            handler=lambda data: self.update_test_outcome(data),
        )
        self.action_collect_tests()
        self.border_title = Text.from_markup(
            " :hourglass_not_done: 0 | :x: 0 | :white_check_mark: 0 | :next_track_button: 0 "
        )

        return super().on_mount()

    @work(thread=True)
    def action_collect_tests(self):
        import subprocess

        subprocess.run(
            ["pytest", "--co"],
            # ["uv", "run", "--with", "../ayu", "-U", "pytest", "--co"],
            capture_output=True,
        )

    def build_tree(self, collection_data: dict[Any, Any]):
        if collection_data:
            self.clear()
            self.update_tree(tree_data=collection_data["tree"])

    def update_tree(self, *, tree_data: dict[Any, Any]):
        parent = self.root

        def add_children(child_list: list[dict[Any, Any]], parent_node: TreeNode):
            for child in child_list:
                if child["children"]:
                    new_node = parent_node.add(
                        label=child["name"], data=child, expand=True
                    )
                    add_children(child_list=child["children"], parent_node=new_node)
                else:
                    new_node = parent_node.add_leaf(label=child["name"], data=child)

        for key, value in tree_data.items():
            if isinstance(value, dict) and "children" in value and value["children"]:
                node: TreeNode = parent.add(key, data=value)
                self.select_node(node)
                add_children(value["children"], node)
            else:
                parent.add_leaf(key, data=key)

    def update_test_outcome(self, test_result: dict):
        for node in self._tree_nodes.values():
            if node.data and (node.data.get("nodeid") == test_result.get("nodeid")):
                outcome = test_result["outcome"]
                # node.label = f"{node.label} {OUTCOME_SYMBOLS[outcome]}"
                node.data["status"] = outcome
                node.label = self.update_node_label(node=node)
                self.count_queue -= 1
                match outcome:
                    case "passed":
                        self.count_passed += 1
                    case "failed":
                        self.count_failed += 1
                    case "skipped":
                        self.count_skipped += 1

    def mark_tests_as_running(self, nodeids: list[str]) -> None:
        self.count_queue = 0
        self.count_passed = 0
        self.count_skipped = 0
        self.count_failed = 0
        for node in self._tree_nodes.values():
            if (
                node.data
                # and isinstance(node.data, dict)
                and (node.data.get("nodeid") in nodeids)
            ):
                # node.label = f"{node.data['name']} {OUTCOME_SYMBOLS['queued']}"
                node.data["status"] = "queued"
                node.label = self.update_node_label(node=node)
                self.count_queue += 1

    def on_tree_node_selected(self, event: Tree.NodeSelected):
        event.node.visible = False
        ...
        # self.notify(f"{event.node.data['name']}")
        # self.scroll_to_node()
        # Run Test

    def action_mark_test(
        self, node: TreeNode | None = None, parent_val: bool | None = None
    ):
        if node is None:
            node = self.cursor_node

        if parent_val is None:
            parent_val = not node.data["favourite"]

        if node.children:
            node.data["favourite"] = parent_val
            node.label = self.update_node_label(node=node)
            for child in node.children:
                self.action_mark_test(node=child, parent_val=parent_val)
        else:
            node.data["favourite"] = parent_val
            node.label = self.update_node_label(node=node)

        if not node.data["favourite"]:
            parent_node = node.parent
            while parent_node.data is not None:
                parent_node.data["favourite"] = node.data["favourite"]
                parent_node.label = self.update_node_label(node=parent_node)
                parent_node = parent_node.parent

    def update_node_label(self, node: TreeNode) -> str:
        fav_substring = "⭐ " if node.data["favourite"] else ""
        status_substring = (
            f" {OUTCOME_SYMBOLS[node.data['status']]}" if node.data["status"] else ""
        )

        return f"{fav_substring}{node.data['name']}{status_substring}"

    def on_mouse_move(self):
        if self.hover_line != -1:
            data = self._tree_lines[self.hover_line].node.data
            self.tooltip = get_nice_tooltip(node_data=data)

    def watch_count_queue(self):
        symbol = "hourglass_not_done" if self.count_queue > 0 else "hourglass_done"
        self.border_title = Text.from_markup(
            f" :{symbol}: {self.count_queue} | :x: {self.count_failed}"
            + f"| :white_check_mark: {self.count_passed} | :next_track_button: {self.count_skipped} "
        )

    def watch_count_passed(self):
        symbol = "hourglass_not_done" if self.count_queue > 0 else "hourglass_done"
        self.border_title = Text.from_markup(
            f" :{symbol}: {self.count_queue} | :x: {self.count_failed}"
            + f"| :white_check_mark: {self.count_passed} | :next_track_button: {self.count_skipped} "
        )

    def watch_count_failed(self):
        symbol = "hourglass_not_done" if self.count_queue > 0 else "hourglass_done"
        self.border_title = Text.from_markup(
            f" :{symbol}: {self.count_queue} | :x: {self.count_failed}"
            + f"| :white_check_mark: {self.count_passed} | :next_track_button: {self.count_skipped} "
        )

    def watch_count_skipped(self):
        symbol = "hourglass_not_done" if self.count_queue > 0 else "hourglass_done"
        self.border_title = Text.from_markup(
            f" :{symbol}: {self.count_queue} | :x: {self.count_failed}"
            + f"| :white_check_mark: {self.count_passed} | :next_track_button: {self.count_skipped} "
        )
