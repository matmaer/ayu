from textual import work
from textual.binding import Binding
from textual.widgets import Tree


class TestTree(Tree):
    BINDINGS = [Binding("r", "refresh_tree", "Refresh")]

    def on_mount(self):
        self.root.add_leaf(
            label="Test",
            data={"bla": 1},
        )

        self.root.add("blabla")
        return super().on_mount()

    @work(thread=True)
    def action_refresh_tree(self):
        import subprocess

        subprocess.run(["pytest", "--co"], capture_output=True)
