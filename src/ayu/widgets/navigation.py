from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ayu.app import AyuApp
from textual import work
from textual.reactive import reactive
from textual.binding import Binding
from textual.widgets import Tree
from textual.widgets.tree import TreeNode
from rich.text import Text

from ayu.utils import (
    EventType,
    NodeType,
    TestOutcome,
    get_nice_tooltip,
    run_test_collection,
)
from ayu.constants import OUTCOME_SYMBOLS


class TestTree(Tree):
    app: "AyuApp"
    BINDINGS = [
        Binding("r", "collect_tests", "Refresh"),
        Binding("j,down", "cursor_down"),
        Binding("k,up", "cursor_up"),
        Binding("f", "mark_test_as_fav", "⭐ Mark"),
    ]
    show_root = False
    auto_expand = True
    guide_depth = 2

    counter_queued: reactive[int] = reactive(0)
    counter_passed: reactive[int] = reactive(0)
    counter_failed: reactive[int] = reactive(0)
    counter_skipped: reactive[int] = reactive(0)
    counter_marked: reactive[int] = reactive(0)

    filtered_data_test_tree: reactive[dict] = reactive({}, init=False)
    filtered_counter_total_tests: reactive[int] = reactive(0, init=False)
    filter: reactive[dict] = reactive(
        {
            "show_favourite": True,
            "show_failed": True,
            "show_skipped": True,
            "show_passed": True,
        },
        init=False,
    )

    def on_mount(self):
        self.app.dispatcher.register_handler(
            event_type=EventType.SCHEDULED,
            handler=lambda data: self.mark_tests_as_running(data),
        )
        self.app.dispatcher.register_handler(
            event_type=EventType.OUTCOME,
            handler=lambda data: self.update_test_outcome(data),
        )

        self.action_collect_tests()

        return super().on_mount()

    def watch_filtered_counter_total_tests(self):
        self.update_border_title()

    def watch_filtered_data_test_tree(self):
        if self.filtered_data_test_tree:
            self.build_tree()

    @work(thread=True)
    def action_collect_tests(self):
        run_test_collection()

    def build_tree(self):
        self.clear()
        self.reset_status_counters()
        self.counter_marked = 0
        self.update_tree(tree_data=self.filtered_data_test_tree)

    def update_tree(self, *, tree_data: dict[Any, Any]):
        parent = self.root

        def add_children(child_list: list[dict[Any, Any]], parent_node: TreeNode):
            for child in child_list:
                if child["children"]:
                    new_node = parent_node.add(
                        label=child["name"], data=child, expand=True
                    )
                    # Update labels?
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
            if node.data and (node.data["nodeid"] == test_result["nodeid"]):
                outcome = test_result["outcome"]
                # node.label = f"{node.label} {OUTCOME_SYMBOLS[outcome]}"
                node.data["status"] = outcome
                node.label = self.update_test_node_label(node=node)
                self.counter_queued -= 1
                match outcome:
                    case TestOutcome.PASSED:
                        self.counter_passed += 1
                    case TestOutcome.FAILED:
                        self.counter_failed += 1
                    case TestOutcome.SKIPPED:
                        self.counter_skipped += 1

                self.update_collapse_state_on_test_run(node=node)

    def update_collapse_state_on_test_run(self, node: TreeNode):
        if node.parent.data["type"] == NodeType.CLASS:
            self.update_collapse_state_on_test_run(node=node.parent)
        if self.all_child_tests_passed(parent=node.parent):
            # node.parent.collapse()
            node.parent.label = self.update_mod_class_node_label(node=node.parent)
            node.parent.label = f"[green]{node.parent.label}[/]"
        else:
            node.parent.expand_all()
            node.parent.label = self.update_mod_class_node_label(node=node.parent)
            node.parent.label = f"[red]{node.parent.label}[/]"

    def all_child_tests_passed(self, parent: TreeNode):
        return all(
            [
                self.all_child_tests_passed(parent=child)
                if child.data["type"] == NodeType.CLASS
                else child.data["status"] in [TestOutcome.PASSED, TestOutcome.QUEUED]
                for child in parent.children
            ]
        )

    def reset_status_counters(self) -> None:
        self.counter_queued = 0
        self.counter_passed = 0
        self.counter_skipped = 0
        self.counter_failed = 0

    def mark_tests_as_running(self, nodeids: list[str]) -> None:
        self.root.expand_all()
        self.reset_status_counters()
        for node in self._tree_nodes.values():
            if node.data and (node.data["nodeid"] in nodeids):
                node.data["status"] = TestOutcome.QUEUED
                node.label = self.update_test_node_label(node=node)
                self.counter_queued += 1

    def on_tree_node_selected(self, event: Tree.NodeSelected):
        ...
        # Run Test

    def action_mark_test_as_fav(
        self, node: TreeNode | None = None, parent_val: bool | None = None
    ):
        # mark filtered tree as fav
        # self.app.data_test_tree['ayu']["children"][0]["favourite"] = True

        # if no node given, select node under cursor
        if node is None:
            node = self.cursor_node

        if parent_val is None:
            parent_val = not node.data["favourite"]

        # mark all childs the same as parent
        if node.children:
            node.data["favourite"] = parent_val
            node.label = self.update_test_node_label(node=node)
            for child in node.children:
                self.action_mark_test_as_fav(node=child, parent_val=parent_val)
        else:
            if node.data["favourite"] != parent_val:
                self.counter_marked += 1 if parent_val else -1
            node.data["favourite"] = parent_val
            node.label = self.update_test_node_label(node=node)

        if not node.data["favourite"]:
            parent_node = node.parent
            while parent_node.data is not None:
                parent_node.data["favourite"] = node.data["favourite"]
                parent_node.label = self.update_test_node_label(node=parent_node)
                parent_node = parent_node.parent

    def update_mod_class_node_label(self, node: TreeNode) -> str:
        counter_childs_tests = len(
            [
                child
                for child in node.children
                if child.data["type"] in [NodeType.FUNCTION, NodeType.COROUTINE]
            ]
        )
        # Misses Class Case
        counter_childs_test_passed = len(
            [
                child
                for child in node.children
                if child.data["status"] == TestOutcome.PASSED
            ]
        )
        fav_substring = "⭐ " if node.data["favourite"] else ""
        if counter_childs_test_passed == counter_childs_tests:
            node.collapse()

        return f"{fav_substring}{node.data['name']} ({counter_childs_test_passed}/{counter_childs_tests})"

    def update_test_node_label(self, node: TreeNode) -> str:
        fav_substring = "⭐ " if node.data["favourite"] else ""
        status_substring = (
            f" {OUTCOME_SYMBOLS[node.data['status']]}" if node.data["status"] else ""
        )

        return f"{fav_substring}{node.data['name']}{status_substring}"

    def on_mouse_move(self):
        return
        if self.hover_line != -1:
            data = self._tree_lines[self.hover_line].node.data
            self.tooltip = get_nice_tooltip(node_data=data)

    def watch_counter_queued(self):
        self.update_border_title()

    def watch_counter_passed(self):
        self.update_border_title()

    def watch_counter_failed(self):
        self.update_border_title()

    def watch_counter_skipped(self):
        self.update_border_title()

    def watch_counter_marked(self):
        self.update_border_title()

    def update_border_title(self):
        symbol = "hourglass_not_done" if self.counter_queued > 0 else "hourglass_done"
        tests_to_run = (
            self.app.counter_total_tests
            if not self.counter_marked
            else f":star: {self.counter_marked}/{self.app.counter_total_tests}"
        )

        self.border_title = Text.from_markup(
            f" :{symbol}: {self.counter_queued} | :x: {self.counter_failed}"
            + f" | :white_check_mark: {self.counter_passed} | :next_track_button: {self.counter_skipped}"
            + f" | Tests to run {tests_to_run} "
        )

    @property
    def marked_tests(self):
        marked_tests = []
        for node in self._tree_nodes.values():
            if (
                node.data
                and (node.data["type"] in [NodeType.FUNCTION, NodeType.COROUTINE])
                and node.data["favourite"]
            ):
                marked_tests.append(node.data["nodeid"])
        return marked_tests

    def reset_test_results(self):
        self.reset_status_counters()
        for node in self._tree_nodes.values():
            if (
                node.data
                and (node.data["type"] in [NodeType.FUNCTION, NodeType.COROUTINE])
                and node.data["status"]
            ):
                node.data["status"] = ""
                node.label = self.update_test_node_label(node=node)
            elif node.data and (node.data["type"] in [NodeType.MODULE, NodeType.CLASS]):
                node.label = self.update_test_node_label(node=node)
