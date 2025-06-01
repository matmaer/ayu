[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI-Server](https://img.shields.io/pypi/v/ayu.svg)](https://pypi.org/project/ayu/)
[![Pyversions](https://img.shields.io/pypi/pyversions/ayu.svg)](https://pypi.python.org/pypi/ayu)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/ayu)](https://pepy.tech/project/ayu)
[![Coverage Status](https://coveralls.io/repos/github/Zaloog/ayu/badge.svg?branch=main)](https://coveralls.io/github/Zaloog/ayu?branch=main)

# Ayu
Ayu is a TUI and pytest-plugin, which allows you to run your pytest tests in a more interactive
fashion in your terminal.


![image](https://raw.githubusercontent.com/Zaloog/ayu/main/images/main_screen.png)

## How does it work
The application starts a local websocket server at `localhost:1337` and the plugin sends data about
collected tests/plugins/results to the app.

# Requirements & Usage
Ayu needs your project to be uv-managed and pytest to be installed.
It utilizes [uv] in the background to run pytest commands.
Concrete it runs `uv run --with ayu pytest [PYTEST-OPTION]` to utilize your python environment and installs the
plugin temporary on the fly to send the data to the TUI, without changing your local environment
or adding dependencies to your project.

```bash
uvx ayu
```

[uv]: https://docs.astral.sh/uv
