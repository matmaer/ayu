import pytest
from pathlib import Path
from ayu.command_builder import Plugin, build_command

not_installed_cov_plugin = Plugin(
    name="pytest-cov",
    version="0.0.1",
    is_installed=False,
    options=["--cov src/ayu", "--report term-missing"],
)


@pytest.mark.parametrize(
    "plugins,tests_to_run,pytest_options,expected_command",
    (
        [None, "", None, "uv run pytest"],
        [
            [not_installed_cov_plugin],
            "",
            None,
            "uv run --with pytest-cov pytest --cov src/ayu --report term-missing",
        ],
        [
            None,
            Path("tests/test_cases"),
            None,
            "uv run pytest tests/test_cases",
        ],
        [None, "", ["--co", "--color=yes"], "uv run pytest --co --color=yes"],
    ),
)
def test_build_command(plugins, tests_to_run, pytest_options, expected_command):
    command = build_command(
        plugins=plugins,
        pytest_options=pytest_options,
        tests_to_run=tests_to_run,
    )
    assert command == expected_command
