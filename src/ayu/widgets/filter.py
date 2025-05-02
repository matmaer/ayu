from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button

from rich.text import Text
from textual_slidecontainer import SlideContainer
from textual_tags import Tags


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

    def compose(self):
        yield TagFilter(tag_values=["bla", "bli", "blo"], id="tags_filter")
        yield ResultFilter(id="horizontal_result_filter").data_bind(
            test_results_ready=TreeFilter.test_results_ready
        )


class ResultFilter(Horizontal):
    test_results_ready: reactive[bool] = reactive(False, init=False)

    def watch_test_results_ready(self):
        if not self.test_results_ready:
            self.border_title = Text.from_markup("No Tests have been run yet")
        else:
            self.border_title = Text.from_markup(
                ":magnifying_glass_tilted_right: Test Result Filter (click to toggle)"
            )
        display_style = "block" if self.test_results_ready else "none"
        self.query_children(".filter-button").set_styles(f"display:{display_style};")
        self.query_children(Button).last().display = not self.test_results_ready

    def compose(self):
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
        yield Button(
            "Result Filter is available once tests are run",
            variant="primary",
            id="button_info",
        )


class FilterButton(Button):
    """Button for filtering the TestTree"""

    filter_is_active: reactive[bool] = reactive(True)

    def on_button_pressed(self):
        self.filter_is_active = not self.filter_is_active

    def watch_filter_is_active(self):
        self.variant = "success" if self.filter_is_active else "error"


class TagFilter(Tags): ...
