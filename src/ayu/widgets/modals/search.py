from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from ayu.app import AyuApp
from textual.message import Message
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.widgets import Input, Footer, Label
from textual.content import Content
from textual.containers import Center

from textual_autocomplete import AutoComplete, DropdownItem, TargetState

from ayu.utils import NodeType


class SearchAutoComplete(AutoComplete):
    app: "AyuApp"

    def get_candidates(self, target_state: TargetState) -> list[DropdownItem]:
        # Filter candidates based on target_state.text
        nodes = self.app.query_one("#testtree").test_nodes
        prefix_bg = "$surface-lighten-3"
        if target_state.text.startswith(":"):
            return [
                DropdownItem(
                    main=Content.from_markup(
                        f"[on {prefix_bg}]{node_type.value}[/][{prefix_bg}]\ue0b4[/] "
                    )
                )
                for node_type in NodeType
            ]
        return [
            DropdownItem(
                main=f"{node.data['nodeid']}",
                prefix=Content.from_markup(
                    f"[on {prefix_bg}]{node.data['type']}[/][{prefix_bg}]\ue0b4[/] {'⭐' if node.data['favourite'] else ''}"
                ),
            )
            for node in nodes[1:]
        ]

    def get_search_string(self, target_state: TargetState) -> str:
        # get only part after certain filter
        if target_state.text.startswith(":"):
            if " " in target_state.text:
                return target_state.text.split(":")[1].split(" ")[1]
            return target_state.text.split(":")[1]
        return target_state.text[: target_state.cursor_position]

    # Override to prevent aligning with input cursor
    def _align_to_target(self) -> None:
        return


class ModalSearch(ModalScreen):
    app: "AyuApp"

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close", show=True),
        Binding(
            "ctrl+j", "navigate_highlight('down')", "down", priority=True, show=True
        ),
        Binding("ctrl+k", "navigate_highlight('up')", "up", priority=True, show=True),
        Binding("ctrl+f", "mark_as_fav", "⭐ Mark", priority=True, show=True),
    ]

    class Marked(Message):
        def __init__(self, nodeid: str) -> None:
            self.nodeid = nodeid
            super().__init__()

        @property
        def control(self):
            return self.nodeid

    def compose(self):
        with Center():
            yield Label("Search for tests")
            yield Input(id="input_search")
            yield Footer()
            yield SearchAutoComplete(
                target="#input_search",
            )

    def action_navigate_highlight(self, direction: Literal["up", "down"]):
        """go to next hightlight in completion option list"""
        if not isinstance(self.app.focused, Input):
            return
        option_list = self.query_one(SearchAutoComplete).option_list
        displayed = self.query_one(SearchAutoComplete).display
        highlighted = option_list.highlighted
        int_direction = 1 if direction == "down" else -1

        if displayed:
            highlighted = (highlighted + int_direction) % option_list.option_count
        else:
            self.query_one(SearchAutoComplete).display = True
            highlighted = 0

        option_list.highlighted = highlighted

    def get_last_state(self, highlighted, scroll_y):
        autocomplete = self.query_one(SearchAutoComplete)
        target_state = autocomplete._get_target_state()

        search_string = autocomplete.get_search_string(target_state)
        autocomplete._rebuild_options(target_state, search_string)

        autocomplete.option_list.highlighted = highlighted
        autocomplete.option_list.scroll_y = scroll_y

    def action_mark_as_fav(self):
        option_list = self.query_one(SearchAutoComplete).option_list
        # displayed = self.query_one(SearchAutoComplete).display

        # Get current hightlight and Scrollposition
        highlighted = option_list.highlighted
        scroll_y = option_list.scroll_y

        node_to_mark = option_list.options[highlighted].value
        self.post_message(self.Marked(nodeid=node_to_mark))

        # Get rebuild options to display changes
        self.set_timer(
            delay=0.05,
            callback=lambda: self.get_last_state(
                highlighted=highlighted, scroll_y=scroll_y
            ),
        )

    # def check_action(self):
    #     ...
