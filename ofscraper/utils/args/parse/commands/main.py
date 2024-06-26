import cloup as click

from ofscraper.utils.args.parse.bundles.advanced_common import advanced_args
from ofscraper.utils.args.parse.bundles.common import common_args
from ofscraper.utils.args.parse.bundles.main import main_program_args


@click.group(
    help="OF-Scraper Options",
    context_settings=dict(help_option_names=["-h", "--help"]),
    invoke_without_command=True,
)
@common_args
@main_program_args
@advanced_args
@click.pass_context
def program(ctx, *args, **kwargs):
    return ctx.params, ctx.info_name
