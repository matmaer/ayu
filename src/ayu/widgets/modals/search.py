from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from ayu.app import AyuApp
from textual.message import Message
from textual.events import Key
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.widgets import Input, Footer, Label
from textual.content import Content
from textual.containers import Center

from textual_autocomplete import AutoComplete, DropdownItem, TargetState

from ayu.utils import NodeType


class SearchInput(Input):
    filtered_node_types: reactive[list] = reactive([])

    def on_key(self, event: Key):
        if event.key == "backspace":
            if not self.value and self.filtered_node_types:
                self.filtered_node_types.pop()
                self.mutate_reactive(SearchInput.filtered_node_types)
                # Fix error showing latest autocompletes if backspacing from 2 elements

    def watch_filtered_node_types(self):
        if self.filtered_node_types:
            hint_substring = (
                f"(press `backspace` to remove {self.filtered_node_types[-1]})"
            )
            self.placeholder = f"Search only for tests of type {', '.join(self.filtered_node_types)} {hint_substring}"
        else:
            self.placeholder = "Press ':' to filter for different NodeTypes"


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
                        f"[{prefix_bg} on {prefix_bg}]:[/][on {prefix_bg}]{node_type.value}[/][{prefix_bg}]\ue0b4[/]"
                    )
                )
                for node_type in NodeType
                if node_type not in self.target.filtered_node_types
            ]
        return [
            DropdownItem(
                main=f"{node.data['nodeid']}",
                prefix=Content.from_markup(
                    f"[on {prefix_bg}] {node.data['type']}[/][{prefix_bg}]\ue0b4[/] {'⭐' if node.data['favourite'] else ''}"
                ),
            )
            for node in nodes[1:]
            if node.data["type"] in (self.target.filtered_node_types or NodeType)
            # if node.data['type'] in
        ]

    def get_search_string(self, target_state: TargetState) -> str:
        # get only part after certain filter
        if target_state.text.startswith(":"):
            return target_state.text
        return target_state.text[: target_state.cursor_position]

    # Add Filter choice
    def post_completion(self) -> None:
        value = self.target.value
        if value[1:-1] in NodeType:
            self.target.filtered_node_types.append(self.target.value[1:-1])
            self.target.mutate_reactive(SearchInput.filtered_node_types)
            self.target.clear()
            self.set_timer(0.05, self.action_show)
        self.action_hide()

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
            yield SearchInput(id="input_search")
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

    def on_input_submitted(self, event: Input.Submitted):
        # self.notify(f'{event.input.value}')
        self.dismiss(result=self.query_one(SearchInput).value)
