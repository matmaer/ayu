from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ayu.app import AyuApp
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.widgets import Placeholder


class ModalPlugin(ModalScreen):
    app: "AyuApp"

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close", show=True),
    ]

    def compose(self):
        yield Placeholder("Test")
