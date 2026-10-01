import argparse
import logging
import sys

from internetarchive import configure

from anything_finder.iaaf_types import MEDIA_TYPES
from anything_finder.search import search_pipeline


def main():  # pragma: no cover
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--config",
        "--configure",
        action="store_true",
        help="Configure authentication to Internet Archive.  \
            Ignores all other arguments.",
    )
    argparser.add_argument(
        "--media_type",
        "--media-type",
        "--type",
        type=str,
        choices=MEDIA_TYPES,
        nargs="?" if ("--config" in sys.argv or "--version" in sys.argv) else None,
        help="Media type to search for.  Always required.",
    )
    argparser.add_argument(
        "--query_all",
        "--query-all",
        action="store_true",
        help="Modifies title argument to be a query.  \
            In this case, it's not a search on title, \
                but globally on all metadata.",
    )
    argparser.add_argument(
        "title",
        nargs="?" if ("--config" in sys.argv or "--version" in sys.argv) else None,
        help="Title to search for.  Always required.",
    )
    argparser.add_argument(
        "--subject", type=str, default=None, help="Optional subject to search for."
    )
    argparser.add_argument(
        "--min_size",
        "--min-size",
        type=str,
        default="0MB",
        help="Minimum size of item to search for.  \
            Supports expressions in MB or GB, like 1MB or 1GB.",
    )
    argparser.add_argument(
        "--max_size",
        "--max-size",
        type=str,
        default="1000GB",
        help="Maximum size of item to search for.  \
            Supports expressions in MB or GB, like 1MB or 1GB.",
    )
    argparser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )
    argparser.add_argument(
        "--version",
        action="store_true",
        help="Print the version.",
    )

    args = argparser.parse_args()

    # Debug catches a lot of lower level stuff from IA, which we don't need right now.
    # In the future, may consider additional verbosity levels.
    logging.basicConfig(level=(logging.INFO if args.verbose else logging.WARN))

    if args.config:
        print("Enter your Internet Archive credentials.")
        configure()
        exit()

    if args.version:
        from anything_finder import __version__

        print(__version__)
        exit()

    search_pipeline(
        title=args.title,
        media_type=args.media_type,
        min_size=args.min_size,
        max_size=args.max_size,
        subject=args.subject,
        query_all=args.query_all,
    )


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
