from pathlib import Path
from dataclasses import dataclass


@dataclass
class Plugin:
    name: str
    version: str
    is_installed: bool
    options: list[str]


def build_command(
    is_tool: bool, plugins: list[Plugin], tests_to_run: Path | list[str] | None
) -> str:
    command_parts = []

    # install ayu on the fly, if ayu is not installed in the project itself
    substring_uv = "uv run --with ayu" if is_tool else "uv run"
    command_parts.append(substring_uv)

    # if plugins are declared with options, but are not installed in the project install them on the fly
    substring_plugins_to_install = " ".join(
        [f"--with {plugin.name}" for plugin in plugins if not plugin.is_installed]
    )
    command_parts.append(substring_plugins_to_install)

    # pytest call here
    command_parts.append("pytest")

    # plugin options afterwards
    substring_plugin_options = ""
    for plugin in plugins:
        substring_plugin_options += " ".join([option for option in plugin.options])
    command_parts.append(substring_plugin_options)

    # wrap tests in quotes to prevent errors when parametrize
    # args include spaces
    if tests_to_run:
        if isinstance(tests_to_run, Path):
            substring_tests_to_run = tests_to_run.as_posix()
        else:
            substring_tests_to_run = " ".join([f'"{test}"' for test in tests_to_run])
    else:
        substring_tests_to_run = ""
    command_parts.append(substring_tests_to_run)

    # only join non empty substrings
    return " ".join([substring for substring in command_parts if substring])
