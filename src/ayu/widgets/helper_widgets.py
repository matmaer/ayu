from __future__ import annotations

from textual.widgets import Rule, Button
from textual.message import Message


class ToggleRule(Rule):
    class Toggled(Message):
        def __init__(self, togglerule: ToggleRule) -> None:
            self.togglerule: ToggleRule = togglerule
            super().__init__()

        @property
        def control(self) -> ToggleRule:
            return self.togglerule

    def __init__(self, target_widget_id: str, *args, **kwargs) -> None:
        self.target_widget_id = target_widget_id
        super().__init__(*args, **kwargs)

    def compose(self):
        yield Button("[green]Passed[/]")

    def on_button_pressed(self):
        self.post_message(self.Toggled(self))
