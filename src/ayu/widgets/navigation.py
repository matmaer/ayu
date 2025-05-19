from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ayu.app import AyuApp
from textual import work
from textual.reactive import reactive
from rich.style import Style
from textual.binding import Binding
from textual.widgets import Tree
from textual.widgets.tree import TreeNode, TreeDataType

from rich.text import Text, TextType

from ayu.utils import (
    EventType,
    NodeType,
    TestOutcome,
    get_nice_tooltip,
    run_test_collection,
)
from ayu.constants import OUTCOME_SYMBOLS

TOGGLE_STYLE = Style.from_meta({"toggle": True})


class TestTree(Tree):
    app: "AyuApp"
    BINDINGS = [
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
        # init=False,
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
        if self.filtered_data_test_tree:
            self.build_tree()

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
    async def action_collect_tests(self):
        self.app.test_results_ready = False
        await run_test_collection(tests_to_run=self.app.test_path)

    def build_tree(self):
        self.clear()
        self.reset_status_counters()
        self.counter_marked = 0
        self.update_tree(tree_data=self.filtered_data_test_tree)

    def filter_tests(self, tests): ...

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
                    add_children(child_list=child["children"], parent_node=new_node)

                    # if all children were filtered out, remove this node
                    if not new_node.children:
                        new_node.remove()
                else:
                    # TODO Make this cleaner, also check for MODULES to be not displayed
                    if not self.filter["show_favourites"] and child["favourite"]:
                        self.filtered_counter_total_tests -= 1
                        continue
                    if not self.filter["show_passed"] and (
                        child["status"] == TestOutcome.PASSED
                    ):
                        self.filtered_counter_total_tests -= 1
                        continue
                    if not self.filter["show_skipped"] and (
                        child["status"] == TestOutcome.SKIPPED
                    ):
                        self.filtered_counter_total_tests -= 1
                        continue
                    if not self.filter["show_failed"] and (
                        child["status"] == TestOutcome.FAILED
                    ):
                        self.filtered_counter_total_tests -= 1
                        continue

                    parent_node.add_leaf(label=child["name"], data=child)

                    if child["favourite"]:
                        self.counter_marked += 1

                    match child["status"]:
                        case TestOutcome.PASSED:
                            self.counter_passed += 1
                        case TestOutcome.SKIPPED:
                            self.counter_skipped += 1
                        case TestOutcome.FAILED:
                            self.counter_failed += 1

        for key, value in tree_data.items():
            if isinstance(value, dict) and "children" in value and value["children"]:
                node: TreeNode = parent.add(key, data=value)
                node.expand()
                add_children(value["children"], node)
            else:
                parent.add_leaf(key, data=key)

        # set initial cursor line
        self.cursor_line: int = 0 if self.cursor_line < 0 else self.cursor_line

        # TODO remove empty nodes after filtering
        # for node in self._tree_nodes.values():
        #     self.log(f'{node}')
        #     if node:
        #         if node.children:
        #             continue
        #         else:
        #             node.remove()

    def update_test_outcome(self, test_result: dict):
        for node in self._tree_nodes.values():
            if node.data and (node.data["nodeid"] == test_result["nodeid"]):
                outcome = test_result["outcome"]
                node.data["status"] = outcome
                node.refresh()
                node.parent.refresh()
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
                    else child.data["status"] in [TestOutcome.PASSED]
                    for child in parent.children
                ]
            )

        if node.parent.data["type"] == NodeType.CLASS:
            self.update_collapse_state_on_test_run(node=node.parent)
        if all_child_tests_passed(parent=node.parent):
            node.parent.collapse()

    def reset_status_counters(self) -> None:
        self.counter_queued = 0
        self.counter_passed = 0
        self.counter_skipped = 0
        self.counter_failed = 0
        self.filtered_counter_total_tests = self.app.counter_total_tests

    def mark_tests_as_running(self, nodeids: list[str]) -> None:
        self.root.expand_all()
        self.reset_status_counters()
        for node in self._tree_nodes.values():
            if node.data and (node.data["nodeid"] in nodeids):
                node.data["status"] = TestOutcome.QUEUED
                self.counter_queued += 1

    def on_tree_node_selected(self, event: Tree.NodeSelected):
        self.notify(f"{','.join(event.node.data['markers'])}")
        ...
        # Run Test

    def mark_test_as_fav_from_markers(self, marker: str):
        for node in self._tree_nodes.values():
            if node.data and marker in node.data["markers"]:
                self.action_mark_test_as_fav(node=node)

    def action_mark_test_as_fav_from_search(self, nodeid: str):
        node_to_mark = self.get_node_by_nodeid(nodeid=nodeid)
        self.action_mark_test_as_fav(node=node_to_mark)

    @work(thread=True)
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
            node.refresh()
            # self.update_filtered_data_test_tree(
            #     nodeid=node.data["nodeid"],
            #     is_fav=parent_val,
            # )
            for child in node.children:
                self.action_mark_test_as_fav(node=child, parent_val=parent_val)
        else:
            if node.data["favourite"] != parent_val:
                self.counter_marked += 1 if parent_val else -1
            node.data["favourite"] = parent_val
            node.refresh()
            # self.update_filtered_data_test_tree(
            #     nodeid=node.data["nodeid"],
            #     is_fav=parent_val,
            # )
            # self.mutate_reactive(TestTree.filtered_data_test_tree)

        # Unfavourite all parents, if a single child not is not favourited
        if not node.data["favourite"]:
            parent_node = node.parent
            while parent_node.data is not None:
                parent_node.data["favourite"] = node.data["favourite"]
                parent_node.refresh()
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

    def process_label(self, label: TextType) -> Text:
        """Subclassed to handle [/] sequences, e.g. in parametrized tests"""
        text_label = label
        first_line = text_label.split()[0]
        return first_line

    def render_label(
        self, node: TreeNode[TreeDataType], base_style: Style, style: Style
    ) -> Text:
        fav_substring = Text.from_markup("⭐ ") if node.data["favourite"] else Text()
        escaped_name_substring = Text(node.data["name"], style)
        # Render Classes, Modules and Folders
        if node._allow_expand:
            prefix = (
                self.ICON_NODE_EXPANDED if node.is_expanded else self.ICON_NODE,
                base_style + TOGGLE_STYLE,
            )
            amount_test_results = self.get_number_of_tests_queued_of_node(node=node)
            amount_tests_passed = self.get_number_of_passed_tests_of_node(node=node)
            if (
                node.data["type"] in [NodeType.CLASS, NodeType.MODULE]
                and amount_test_results
            ):
                run_status_label = Text(f" {amount_tests_passed}/{amount_test_results}")
                run_label_color = (
                    "green" if amount_tests_passed == amount_test_results else "red"
                )
            else:
                run_status_label = ""
                run_label_color = None

            module_label = Text.assemble(
                prefix,
                fav_substring,
                escaped_name_substring,
                run_status_label,
                style=Style(color=run_label_color),
            )
            module_label.stylize(style)
            return module_label

        # Render Test Labels
        status_substring = Text.from_markup(
            f" {OUTCOME_SYMBOLS[node.data['status']]}" if node.data["status"] else ""
        )
        test_label = Text.assemble(
            fav_substring, escaped_name_substring, status_substring
        )
        return test_label

    def get_number_of_tests_queued_of_node(self, node: TreeNode) -> int:
        return len(
            [
                child
                for child in node.children
                if (child.data["type"] in [NodeType.FUNCTION, NodeType.COROUTINE])
                if child.data["status"]
            ]
        )

    def get_number_of_passed_tests_of_node(self, node: TreeNode) -> int:
        return len(
            [
                child
                for child in node.children
                if child.data["status"] == TestOutcome.PASSED
            ]
        )

    def on_mouse_move(self):
        return
        if self.hover_line != -1:
            data = self._tree_lines[self.hover_line].node.data
            self.tooltip = get_nice_tooltip(node_data=data)

    def highlight_marker_rows(self, marker: str):
        for node in self._tree_nodes.values():
            node._hover = False
            if node.data and (marker in node.data["markers"]):
                node._hover = True
                last_true_line = node.line
                self.refresh()
        self.hover_line = last_true_line

    def update_border_title(self):
        symbol = "hourglass_not_done" if self.counter_queued > 0 else "hourglass_done"
        tests_to_run = (
            self.filtered_counter_total_tests
            if not self.counter_marked
            else f":star: {self.counter_marked}/{self.filtered_counter_total_tests}"
        )

        self.border_title = Text.from_markup(
            f" :{symbol}: {self.counter_queued} | :x: {self.counter_failed}"
            + f" | :white_check_mark: {self.counter_passed} | :next_track_button: {self.counter_skipped}"
            + f" | Tests to run {tests_to_run} "
        )

    def get_node_by_nodeid(self, nodeid: str) -> TreeNode | None:
        for node in self._tree_nodes.values():
            if node.data and (node.data["nodeid"] == nodeid):
                return node
        return None

    @property
    def marked_tests(self):
        # TODO based on self.filtered_data_test_tree,
        # to run tests accordingly when filter is active
        marked_tests = []
        for node in self._tree_nodes.values():
            if (
                node.data
                and (node.data["type"] in [NodeType.FUNCTION, NodeType.COROUTINE])
                and node.data["favourite"]
            ):
                marked_tests.append(node.data["nodeid"])
        return marked_tests

    @property
    def test_nodes(self) -> list[TreeNode]:
        test_nodes = []
        for node in self._tree_nodes.values():
            if node.data:
                test_nodes.append(node)
        return test_nodes

    def reset_test_results(self):
        # reset self.filtered_data_test_tree,
        # to also reset results that were hidden by the filter
        self.reset_status_counters()
        for node in self._tree_nodes.values():
            if node.data:
                node.data["status"] = ""
                node.refresh()
