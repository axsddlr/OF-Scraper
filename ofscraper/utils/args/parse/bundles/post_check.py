import itertools

import cloup as click

import ofscraper.utils.args.parse.arguments.helpers.type as type
from ofscraper.utils.args.parse.bundles.advanced_common import advanced_args
from ofscraper.utils.args.parse.bundles.common import common_args
from ofscraper.utils.args.parse.bundles.helpers.check import check_mode_changes


def post_check_args(func):
    @click.command(
        "post_check",
        short_help="""\b
                Produces a media table from posts with filterable entries and quick downloads""",
        help="""The post_check subcommand gathers information on media content from posts
    It presents this data in a table format with filtering options for focused searches 
    Allows unlocked media entries to be directly downloaded through the table""",
    )
    @common_args
    @click.constraints.require_one(
        click.option(
            "-u",
            "--url",
            help="Scan posts via space or comma seperated list of urls",
            default=None,
            multiple=True,
            type=type.check_modes_strhelper,
            callback=lambda ctx, param, value: (
                list(set(itertools.chain.from_iterable(value))) if value else []
            ),
        ),
        click.option(
            "-f",
            "--file",
            help="Scan posts via a file with line-separated URL(s)",
            default=None,
            type=type.check_modes_filehelper,
            multiple=True,
            callback=lambda ctx, param, value: (
                list(set(itertools.chain.from_iterable(value))) if value else []
            ),
        ),
    )
    @click.option(
        "-fo",
        "--force",
        help="Force retrieval of new posts info from API",
        is_flag=True,
        default=False,
    )
    @click.option(
        "-ca",
        "--check-area",
         "--post",
        "--post",
        "check_area",
        help="Select areas to check (multiple allowed, separated by spaces)",
        default=["Timeline", "Pinned", "Archived","Streams"],
        type=type.post_check_area_helper,
        callback=lambda ctx, param, value: (
        list(set(itertools.chain.from_iterable(value))) if value else []
        ),
        multiple=True,
        )
    
    @advanced_args
    @check_mode_changes
    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        return func(ctx, *args, **kwargs)

    return wrapper
