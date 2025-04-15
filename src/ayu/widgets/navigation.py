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
            "show_favourites": True,
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

    def watch_filter(self):
        self.mutate_reactive(TestTree.filtered_data_test_tree)
        # self.notify(f"from tree: {self.filter}")

    def watch_filtered_counter_total_tests(self):
        self.update_border_title()

    def watch_filtered_data_test_tree(self):
        if self.filtered_data_test_tree:
            self.build_tree()

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
        self.app.refresh_bindings()

    @work(thread=True)
    def action_collect_tests(self):
        self.app.test_results_ready = False
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
                    if not self.filter["show_favourites"] and child["favourite"]:
                        continue
                    new_node = parent_node.add(
                        label=child["name"], data=child, expand=True
                    )
                    new_node.label = self.update_mod_class_node_label(node=new_node)
                    add_children(child_list=child["children"], parent_node=new_node)
                else:
                    # TODO Make this cleaner, also check for MODULES to be not displayed
                    if not self.filter["show_favourites"] and child["favourite"]:
                        continue
                    if not self.filter["show_passed"] and (
                        child["status"] == TestOutcome.PASSED
                    ):
                        continue
                    if not self.filter["show_skipped"] and (
                        child["status"] == TestOutcome.SKIPPED
                    ):
                        continue
                    if not self.filter["show_failed"] and (
                        child["status"] == TestOutcome.FAILED
                    ):
                        continue
                    new_node = parent_node.add_leaf(label=child["name"], data=child)
                    new_node.label = self.update_test_node_label(node=new_node)
                    if child["favourite"]:
                        self.counter_marked += 1

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
                self.update_filtered_data_test_tree(
                    nodeid=node.data["nodeid"], new_status=outcome
                )

    def update_collapse_state_on_test_run(self, node: TreeNode):
        def all_child_tests_passed(parent: TreeNode):
            return all(
                [
                    all_child_tests_passed(parent=child)
                    if child.data["type"] == NodeType.CLASS
                    else child.data["status"]
                    in [TestOutcome.PASSED, TestOutcome.QUEUED]
                    for child in parent.children
                ]
            )

        if node.parent.data["type"] == NodeType.CLASS:
            self.update_collapse_state_on_test_run(node=node.parent)
        if all_child_tests_passed(parent=node.parent):
            node.parent.label = self.update_mod_class_node_label(node=node.parent)
        else:
            node.parent.label = self.update_mod_class_node_label(node=node.parent)

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
        # if no node given, select node under cursor
        if node is None:
            node = self.cursor_node

        if parent_val is None:
            parent_val = not node.data["favourite"]

        # mark all childs the same as parent
        if node.children:
            node.data["favourite"] = parent_val
            node.label = self.update_test_node_label(node=node)
            self.update_filtered_data_test_tree(
                nodeid=node.data["nodeid"],
                is_fav=parent_val,
            )
            for child in node.children:
                self.action_mark_test_as_fav(node=child, parent_val=parent_val)
        else:
            if node.data["favourite"] != parent_val:
                self.counter_marked += 1 if parent_val else -1
            node.data["favourite"] = parent_val
            node.label = self.update_test_node_label(node=node)
            self.update_filtered_data_test_tree(
                nodeid=node.data["nodeid"],
                is_fav=parent_val,
            )
            # self.mutate_reactive(TestTree.filtered_data_test_tree)

        if not node.data["favourite"]:
            parent_node = node.parent
            while parent_node.data is not None:
                parent_node.data["favourite"] = node.data["favourite"]
                parent_node.label = self.update_test_node_label(node=parent_node)
                parent_node = parent_node.parent

    def update_filtered_data_test_tree(
        self,
        nodeid: str,
        is_fav: bool | None = None,
        new_status: TestOutcome | None = None,
    ):
        def update_filtered_node(child_list: list):
            for child in child_list:
                if child["nodeid"] == nodeid:
                    if is_fav is not None:
                        child["favourite"] = is_fav
                    if new_status:
                        child["status"] = new_status
                    return True
                if child["children"]:
                    update_filtered_node(child_list=child["children"])

        for key, val in self.filtered_data_test_tree.items():
            if val["nodeid"] == nodeid:
                if is_fav is not None:
                    val["favourite"] = is_fav
                if new_status:
                    val["status"] = new_status
                return True
            if val["children"]:
                update_filtered_node(child_list=val["children"])

    def update_mod_class_node_label(self, node: TreeNode) -> str:
        counter_childs_tests = len(
            [
                child
                for child in node.children
                if (child.data["type"] in [NodeType.FUNCTION, NodeType.COROUTINE])
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
        count_substring = (
            f"({counter_childs_test_passed}/{counter_childs_tests})"
            if counter_childs_tests > 0
            else ""
        )

        if counter_childs_test_passed != counter_childs_tests:
            node.expand()
            color_style = "red"
        else:
            color_style = "green"
            node.collapse()

        if all([child.data["status"] == "" for child in node.children]):
            color_style = ""
            node.expand()
        return Text.from_markup(
            f"{fav_substring}{node.data['name']} {count_substring}", style=color_style
        )

    def update_test_node_label(self, node: TreeNode) -> str:
        fav_substring = "⭐ " if node.data["favourite"] else ""
        status_substring = (
            f" {OUTCOME_SYMBOLS[node.data['status']]}" if node.data["status"] else ""
        )
        return Text.from_markup(f"{fav_substring}{node.data['name']}{status_substring}")

    def on_mouse_move(self):
        return
        if self.hover_line != -1:
            data = self._tree_lines[self.hover_line].node.data
            self.tooltip = get_nice_tooltip(node_data=data)

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
