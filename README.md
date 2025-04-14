# Ayu

Ayu is a TUI and pytest-plugin, which allows you to run your pytest tests in a more interactive
fashion in your terminal.

It needs your project to be uv-managed cause it utilizes `uv` in the background to run pytest.
Concrete it runs `uv run --with ayu pytest` to utilize your python environment and installs the
plugin on the fly to send the data to the TUI.

# Usage
```bash
uvx ayu
```
