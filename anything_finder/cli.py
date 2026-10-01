import logging

import click
from internetarchive import configure as ia_configure
from pydantic import ValidationError

from anything_finder import __version__
from anything_finder.iaaf_types import MEDIA_TYPES, Size
from anything_finder.search import search_pipeline


def _validate_size(ctx: click.Context, param: click.Parameter, value: str) -> str:
    try:
        Size(size=value)
    except ValidationError as e:
        raise click.BadParameter(e.errors()[0]["msg"]) from e
    return value


@click.group()
@click.version_option(__version__, prog_name="iaaf")
@click.option("--verbose", is_flag=True, help="Enable verbose logging.")
def main(verbose: bool):
    """Internet Archive Anything Finder."""
    # Debug catches a lot of lower level stuff from IA, which we don't need right now.
    # In the future, may consider additional verbosity levels.
    logging.basicConfig(level=logging.INFO if verbose else logging.WARN)


@main.command()
@click.argument("title")
@click.option(
    "--media-type",
    "--media_type",
    "--type",
    "media_type",
    type=click.Choice(MEDIA_TYPES),
    required=True,
    help="Media type to search for.",
)
@click.option(
    "--query-all",
    "--query_all",
    "query_all",
    is_flag=True,
    help="Treat TITLE as a query against all metadata instead of a title search.",
)
@click.option("--subject", default=None, help="Optional subject to search for.")
@click.option(
    "--min-size",
    "--min_size",
    "min_size",
    default="0MB",
    show_default=True,
    callback=_validate_size,
    help="Minimum item size, in MB or GB (e.g. 1MB, 1GB).",
)
@click.option(
    "--max-size",
    "--max_size",
    "max_size",
    default="1000GB",
    show_default=True,
    callback=_validate_size,
    help="Maximum item size, in MB or GB (e.g. 1MB, 1GB).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    show_default=True,
    help="Output format.",
)
def search(
    title: str,
    media_type: str,
    query_all: bool,
    subject: str | None,
    min_size: str,
    max_size: str,
    output_format: str,
):
    """Search Internet Archive for items matching TITLE."""
    search_pipeline(
        title=title,
        media_type=media_type,
        min_size=min_size,
        max_size=max_size,
        subject=subject,
        query_all=query_all,
        output_format=output_format,
    )


@main.command()
def configure():
    """Configure authentication to Internet Archive."""
    click.echo("Enter your Internet Archive credentials.")
    ia_configure()


if __name__ == "__main__":  # pragma: no cover
    main()
