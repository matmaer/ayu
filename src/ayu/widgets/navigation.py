from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ayu.app import AyuApp
from textual import work
from textual.binding import Binding
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from ayu.utils import EventType


class TestTree(Tree):
    app: "AyuApp"
    BINDINGS = [Binding("r", "refresh_tree", "Refresh")]

    def on_mount(self):
        self.app.dispatcher.register_handler(
            event_type=EventType.COLLECTION,
            handler=lambda data: self.build_tree(data),
        )
        self.action_refresh_tree()
        self.auto_expand = True

        return super().on_mount()

    @work(thread=True)
    def action_refresh_tree(self):
        import subprocess

        subprocess.run(["pytest", "--co"], capture_output=True)

    def build_tree(self, collection_data: dict[Any, Any]):
        if collection_data:
            self.clear()
            self.update_tree(tree_data=collection_data["tree"])

    def update_tree(self, *, tree_data: dict[Any, Any]):
        parent = self.root

        def add_children(child_list: list[dict[Any, Any]], parent_node: TreeNode):
            for child in child_list:
                if child["children"]:
                    new_node = parent_node.add(label=child["name"], expand=True)
                    add_children(child_list=child["children"], parent_node=new_node)
                else:
                    parent_node.add_leaf(label=child["name"])

        for key, value in tree_data.items():
            if isinstance(value, dict) and "children" in value and value["children"]:
                node: TreeNode = parent.add(key, expand=True, data=value)
                self.select_node(node)
                add_children(value["children"], node)
            else:
                parent.add_leaf(key, data=key)
