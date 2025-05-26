from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ayu.app import AyuApp

from textual import on, work
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.widgets import (
    Footer,
    Label,
    Switch,
    Select,
    Input,
    Collapsible,
    Rule,
    DataTable,
)
from textual.containers import Horizontal, Vertical, VerticalScroll

from ayu.utils import OptionType, run_plugin_collection


class ModalPlugin(ModalScreen):
    app: "AyuApp"
    plugin_option_dict: reactive[dict] = reactive({}, init=False)
    selected_options_dict: reactive[dict] = reactive({}, init=False)

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close", show=True),
    ]

    @work()
    async def on_mount(self):
        await run_plugin_collection()

    def compose(self):
        with VerticalScroll():
            yield Footer()
            for plugin, plugin_dict in self.app.plugin_option_dict.items():
                with PlugInCollapsible(title=plugin):
                    for option_dict in plugin_dict["options"]:
                        match option_dict["type"]:
                            case OptionType.BOOL:
                                yield BoolOption(option_dict=option_dict)
                            case OptionType.STR:
                                yield StringOption(option_dict=option_dict)
                            case OptionType.LIST:
                                yield ListOption(option_dict=option_dict)
                            case OptionType.SELECTION:
                                yield SelectionOption(option_dict=option_dict)

    def watch_plugin_option_dict(self):
        # self.notify(f'modal: {self.plugin_dict.keys()}', markup=False)
        # Refresh like this turns all other settings to default
        self.refresh(recompose=True)

    def watch_selected_options_dict(self):
        self.notify(f"{self.selected_options_dict}", markup=False, timeout=0.5)


class PlugInCollapsible(Collapsible):
    amount_changed: reactive[int] = reactive(0)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.plugin = self.title

    @on(Switch.Changed)
    @on(Input.Changed)
    @on(Select.Changed)
    @on(DataTable.RowSelected)
    def update_amount(self):
        self.amount_changed = sum(
            [widget.was_changed for widget in self._contents_list if widget.was_changed]
        )

    def watch_amount_changed(self):
        if self.amount_changed > 0:
            amount_str = (
                f"[$success]{self.amount_changed}/{len(self._contents_list)}[/]"
            )
        else:
            amount_str = f"[$error]{self.amount_changed}/{len(self._contents_list)}[/]"
        self.title = f"{amount_str} {self.plugin}"


class BoolOption(Vertical):
    app: "AyuApp"
    option: reactive[str] = reactive("", init=False)
    option_value: reactive[str] = reactive("", init=False)
    complete_option: reactive[str | None] = reactive(None, init=False)
    was_changed: reactive[bool] = reactive(False, init=False)

    def __init__(self, option_dict: dict[str, Any], *args, **kwargs) -> None:
        self.option_dict = option_dict
        super().__init__(*args, **kwargs)
        self.classes = "optionwidget"
        self.option = "".join(option_dict["names"])
        self.option_value = option_dict["default"]

    def on_mount(self):
        self.query_one(Label).tooltip = self.option_dict["help"]
        # Set to current Value
        dest = self.option_dict["dest"]
        if dest != self.option_dict["default"]:
            self.query_one(Switch).value = self.app.selected_options_dict[dest]

    def compose(self):
        with Horizontal():
            yield Label(f"{self.option} [gray]{self.option_dict['dest']}[/]")
            yield Switch(value=self.option_dict["default"])
        yield Rule()
        return super().compose()

    def on_switch_changed(self, event: Switch.Changed):
        self.option_value = event.switch.value

    def watch_option_value(self):
        if self.option_value == self.option_dict["default"]:
            self.complete_option = None
        else:
            self.complete_option = f"{self.option}"

    def watch_was_changed(self):
        if self.was_changed:
            self.query_one(Label).update(
                f"[$success]{self.option}[/] [gray]{self.option_dict['dest']}[/]"
            )
        else:
            self.query_one(Label).update(
                f"{self.option} [gray]{self.option_dict['dest']}[/]"
            )

    # complete option string for the command builder
    def watch_complete_option(self):
        if self.complete_option is None:
            # self.app.options.pop(self.flag)
            self.was_changed = False
        else:
            # self.app.options[self.flag] = self.complete_flag
            self.was_changed = True

        # self.app.update_options()


class StringOption(Vertical):
    app: "AyuApp"
    option: reactive[str] = reactive("", init=False)
    option_value: reactive[str] = reactive("", init=False)
    complete_option: reactive[str | None] = reactive(None, init=False)
    was_changed: reactive[bool] = reactive(False, init=False)

    def __init__(self, option_dict: dict[str, str], *args, **kwargs) -> None:
        self.option_dict = option_dict
        super().__init__(*args, **kwargs)
        self.classes = "optionwidget"
        self.option = "".join(option_dict["names"])
        self.option_value = option_dict["default"]

    def on_mount(self):
        self.query_one(Label).tooltip = self.option_dict["help"]
        # Set to current Value
        dest = self.option_dict["dest"]
        if dest != self.option_dict["default"]:
            value = self.app.selected_options_dict[dest]
            self.query_one(Input).value = f"{value}" if isinstance(value, list) else ""

    def compose(self):
        with Horizontal():
            yield Label(f"{self.option} [gray]{self.option_dict['dest']}[/]")
            yield Input(placeholder=f"default: {self.option_dict['default']}")
        yield Rule()
        return super().compose()

    def on_input_changed(self, event: Input.Changed):
        self.option_value = event.input.value

    def watch_option_value(self):
        if self.option_value in [self.option_dict["default"], ""]:
            self.complete_option = None
        else:
            self.complete_option = f"{self.option}={self.option_value}"

    def watch_was_changed(self):
        if self.was_changed:
            self.query_one(Label).update(
                f"[$success]{self.option}[/] [gray]{self.option_dict['dest']}[/]"
            )
        else:
            self.query_one(Label).update(
                f"{self.option} [gray]{self.option_dict['dest']}[/]"
            )

    def watch_complete_option(self):
        if self.complete_option is None:
            # self.app.options.pop(self.option)
            self.was_changed = False
        else:
            # self.app.options[self.option] = self.complete_option
            self.was_changed = True
        # self.app.update_options()


class SelectionOption(Vertical):
    app: "AyuApp"
    option: reactive[str] = reactive("", init=False)
    option_value: reactive[str] = reactive("", init=False)
    complete_option: reactive[str | None] = reactive(None, init=False)
    was_changed: reactive[bool] = reactive(False, init=False)

    def __init__(self, option_dict: dict[str, str | list], *args, **kwargs) -> None:
        self.option_dict = option_dict
        super().__init__(*args, **kwargs)
        self.classes = "optionwidget"
        self.option = "".join(option_dict["names"])
        self.option_value = option_dict["default"]

    def compose(self):
        with Horizontal():
            yield Label(f"{self.option} [gray]{self.option_dict['dest']}[/]")
            with self.prevent(Select.Changed):
                yield Select(
                    value=self.option_dict["default"],
                    options=(
                        (choice, choice) for choice in self.option_dict["choices"]
                    ),
                    allow_blank=False,
                )
        yield Rule()
        return super().compose()

    def on_mount(self):
        self.query_one(Label).tooltip = self.option_dict["help"]
        # Set to current Value
        dest = self.option_dict["dest"]
        if dest != self.option_dict["default"]:
            self.query_one(Select).value = self.app.selected_options_dict[dest]

    def on_select_changed(self, event: Select.Changed):
        self.option_value = event.select.value

    def watch_option_value(self):
        if self.option_value == self.option_dict["default"]:
            self.complete_option = None
        else:
            self.complete_option = f"{self.option}={self.option_value}"

    def watch_was_changed(self):
        if self.was_changed:
            self.query_one(Label).update(
                f"[$success]{self.option}[/] [gray]{self.option_dict['dest']}[/]"
            )
        else:
            self.query_one(Label).update(
                f"{self.option} [gray]{self.option_dict['dest']}[/]"
            )

    def watch_complete_option(self):
        if self.complete_option is None:
            # self.app.options.pop(self.option)
            self.was_changed = False
        else:
            # self.app.options[self.option] = self.complete_option
            self.was_changed = True
        # self.app.update_options()


class ListOption(Vertical):
    app: "AyuApp"
    option: reactive[str] = reactive("", init=False)
    option_value: reactive[list] = reactive(list, init=False)
    complete_option: reactive[str | None] = reactive(None, init=False)
    was_changed: reactive[bool] = reactive(False, init=False)

    def __init__(self, option_dict: dict[str, list], *args, **kwargs) -> None:
        self.option_dict = option_dict
        super().__init__(*args, **kwargs)
        self.classes = "optionwidget"
        self.option = "".join(option_dict["names"])
        self.option_value = option_dict["default"]

    def on_mount(self):
        self.query_one(Label).tooltip = self.option_dict["help"]
        dest = self.option_dict["dest"]
        dest_values = self.app.selected_options_dict[dest]
        if dest_values != self.option_dict["default"]:
            for value in dest_values:
                self.add_new_value(new_value=value)
            self.parent.parent.update_amount()

    def compose(self):
        with Horizontal():
            yield Label(f"{self.option} [gray]{self.option_dict['dest']}[/]")
            yield Input(placeholder="enter a value and press enter to add to list")
        self.list_table = DataTable(cursor_type="row", show_header=False)
        self.list_table.add_column("option", key="option")
        self.list_table.add_column("remove", key="remove")
        self.list_table.display = False

        yield self.list_table
        yield Rule()
        return super().compose()

    # TODO Add Input validation to prevent adding the same
    def on_input_submitted(self, event: Input.Submitted):
        new_value = event.input.value.strip()
        if new_value:
            self.add_new_value(new_value=new_value)
            event.input.clear()

    def add_new_value(self, new_value):
        if new_value in self.list_table.rows.keys():
            return

        self.list_table.add_row(
            new_value,
            ":cross_mark: click to remove",
            key=new_value,
        )
        self.option_value.append(new_value)
        self.mutate_reactive(ListOption.option_value)

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        self.option_value.remove(event.row_key)
        self.list_table.remove_row(event.row_key)
        self.mutate_reactive(ListOption.option_value)
        # TODO When having a long entry and a scrollbar appears
        # The column widths doesnt reset back

    def watch_option_value(self):
        if self.option_value == self.option_dict["default"]:
            self.complete_option = None
        else:
            if len(self.option_value) == 1:
                self.complete_option = f"{self.option}={self.option_value[0]}"
            else:
                self.complete_option = f'{self.option}="{",".join(self.option_value)}"'

    def watch_was_changed(self):
        if self.was_changed:
            self.query_one(Label).update(
                f"[$success]{self.option}[/] [gray]{self.option_dict['dest']}[/]"
            )
        else:
            self.query_one(Label).update(
                f"{self.option} [gray]{self.option_dict['dest']}[/]"
            )
            self.query_one(Input).focus()
        self.list_table.display = self.was_changed

    def watch_complete_option(self):
        if self.complete_option is None:
            # self.app.options.pop(self.option)
            self.was_changed = False
        else:
            self.notify(f" {self.option} was changed")
            # self.app.options[self.option] = self.complete_option
            self.was_changed = True
        # self.app.update_options()
