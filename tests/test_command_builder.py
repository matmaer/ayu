import pytest
from ayu.command_builder import Plugin, build_command

not_installed_cov_plugin = Plugin(
    name="pytest-cov",
    version="0.0.1",
    is_installed=False,
    options=["--cov src/ayu", "--report term-missing"],
)


@pytest.mark.parametrize(
    "is_tool,plugins,tests_to_run,expected_command",
    (
        [True, [], "", "uv run --with ayu pytest"],
        [
            False,
            [not_installed_cov_plugin],
            "",
            "uv run --with pytest-cov pytest --cov src/ayu --report term-missing",
        ],
    ),
)
def test_build_command(is_tool, plugins, tests_to_run, expected_command):
    command = build_command(
        is_tool=is_tool,
        plugins=plugins,
        tests_to_run=tests_to_run,
    )
    assert command == expected_command
