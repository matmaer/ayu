from ayu.app import AyuApp
import click


@click.group(
    context_settings={"ignore_unknown_options": True}, invoke_without_command=True
)
@click.version_option(prog_name="ayu")
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        app = AyuApp()
        app.run()
    else:
        pass


if __name__ == "__main__":
    cli()
