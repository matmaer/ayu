from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ayu.app import AyuApp
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.widgets import Input
from textual.content import Content

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
                    f"[on {prefix_bg}]{node.data['type']}[/][{prefix_bg}]\ue0b4[/] "
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
        return super().get_search_string(target_state=target_state)

    # Override to prevent aligning with input cursor
    def _align_to_target(self) -> None:
        return


class ModalSearch(ModalScreen):
    app: "AyuApp"

    BINDINGS = [Binding("escape", "app.pop_screen")]

    def compose(self):
        yield Input(id="input_search")
        yield SearchAutoComplete(
            target="#input_search",
        )
