from ayu.app import AyuApp
import click


@click.group(
    context_settings={"ignore_unknown_options": True}, invoke_without_command=True
)
@click.version_option(prog_name="ayu")
@click.pass_context
@click.argument(
    "tests_path", type=click.Path(exists=True, file_okay=False), required=False
)
def cli(ctx, tests_path):
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
