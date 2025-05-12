from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ayu.app import AyuApp

from textual.containers import Horizontal, Vertical
from textual.widgets import Label, Placeholder

# from ayu.utils import EventType


class CoverageExplorer(Vertical):
    app: "AyuApp"

    def on_mount(self):
        self.display = False

        # self.app.dispatcher.register_handler(
        #     event_type=EventType.COVERAGE,
        #     handler=lambda msg: self.update_test(msg),
        # )

    def compose(self):
        yield CoverageLabel("[bold]Test Coverage[/]")
        with Horizontal():
            with Vertical():
                yield CoverageTable("Table")
                yield CoverageFilePreview("Preview")
            yield MissingLinesTable("LInes")

    def update_test(self, msg):
        self.query_one(CoverageLabel).update(f"{msg}")


class CoverageLabel(Label):
    "Label for log"


class CoverageTable(Placeholder):
    """General Table for Coverage Information"""


class MissingLinesTable(Placeholder):
    """Table for Missing Lines"""


class CoverageFilePreview(Placeholder):
    """Preview of Lines in source file"""
