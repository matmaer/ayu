from pathlib import Path
import click

from ayu.app import AyuApp
from ayu.utils import uv_is_installed, project_is_uv_managed, ayu_is_run_as_tool


@click.group(
    context_settings={"ignore_unknown_options": True}, invoke_without_command=True
)
@click.version_option(prog_name="ayu")
@click.pass_context
@click.argument(
    "tests_path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=False,
)
def cli(ctx, tests_path):
    if ayu_is_run_as_tool():
        print("ayu as tool")
    else:
        print("ayu as dependency")
    # return
    if not uv_is_installed():
        print("uv_not_installed, please install uv to use ayu")
        return
    if not project_is_uv_managed():
        print("Your project is not a valid python project")
        print("no pyproject.toml file detected")
        return

    if tests_path:
        app = AyuApp(test_path=tests_path)
        app.run()
    elif ctx.invoked_subcommand is None:
        app = AyuApp()
        app.run()
    else:
        pass


if __name__ == "__main__":
    cli()
