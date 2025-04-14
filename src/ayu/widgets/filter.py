from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button

from rich.text import Text
from textual_slidecontainer import SlideContainer


class TreeFilter(SlideContainer):
    test_results_ready: reactive[bool] = reactive(False, init=False)

    def __init__(self, *args, **kwargs):
        super().__init__(
            slide_direction="down",
            floating=False,
            start_open=False,
            duration=0.5,
            *args,
            **kwargs,
        )

    def on_mount(self):
        self.border_title = Text.from_markup(
            ":magnifying_glass_tilted_right: Test Result Filter (click to toggle)"
        )

    def watch_test_results_ready(self):
        self.query_one("#horizontal_filter_buttons").set_class(
            not self.test_results_ready, "hidden"
        )
        self.query_one("#horizontal_filter_message").set_class(
            self.test_results_ready, "hidden"
        )

    def compose(self):
        with Horizontal(id="horizontal_filter_buttons", classes="hidden"):
            yield FilterButton(
                label=Text.from_markup("Marked: :star:"),
                id="button_filter_favourites",
                classes="filter-button",
            )
            yield FilterButton(
                label=Text.from_markup("Passed: :white_check_mark:"),
                id="button_filter_passed",
                classes="filter-button",
            )
            yield FilterButton(
                label=Text.from_markup("Failed: :x:"),
                id="button_filter_failed",
                classes="filter-button",
            )
            yield FilterButton(
                label=Text.from_markup("Skipped: [on yellow]:next_track_button: [/]"),
                id="button_filter_skipped",
                classes="filter-button",
            )
        with Horizontal(id="horizontal_filter_message"):
            yield Button()


class FilterButton(Button):
    class Pressed(Button.Pressed): ...

    """Button for filtering the TestTree"""

    filter_is_active: reactive[bool] = reactive(True)

    def on_button_pressed(self):
        self.filter_is_active = not self.filter_is_active

    def watch_filter_is_active(self):
        self.variant = "success" if self.filter_is_active else "error"
