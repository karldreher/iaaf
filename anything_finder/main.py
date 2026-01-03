import argparse
import json
import logging
import sys

import yaml
from internetarchive import Item, configure, get_session

from anything_finder.iaaf_types import MEDIA_TYPES, Size

session = get_session()
logger = logging.getLogger(__name__)


class ArchiveItem:
    def __init__(self, item: Item):
        self.item = item
        self.metadata = item.metadata
        self.title = item.metadata["title"]
        self.item_size = item.item_size
        self.url = f"http://archive.org/details/{self}"
        self.dict = {
            "title": self.title,
            "item_size": self.item_size,
            "url": self.url,
        }

    def __repr__(self):
        return self.metadata["identifier"]

    def download(self):
        self.item.download()

    def download_url(self):
        self.item.download(dry_run=True)

    @property
    def output(self, format: str = "yaml"):
        if format == "yaml":
            return yaml.dump([self.dict], sort_keys=False)
        if format == "json":
            return json.dumps(self.dict)
        raise ValueError("Output format must be yaml or json.")


class ArchiveSearch:
    def __init__(
        self,
        title: str,
        media_type: str,
        min_size: Size = Size(size=0),
        max_size: Size = Size(size=1000000000000),
        subject: str | None = None,
        query_all: bool = False,
    ):
        """
        Search Internet Archive for items matching the title.
        @param title: Title to search for.
        @param media_type: Media type to search for.
        @param min_size: Minimum size of item to search for.
        @param subject: Optional subject to search for.
        @param query_all: Query modifier for title.  \
            When True, it's not a title, but a general query.

        """
        # Title may not default to None, as it is required.
        # But, it can be modified by query_all.
        self.title = f'title:"{title}"' if not query_all else f"({title})"
        self.subject = f'subject:"{subject}"' if subject else None
        # IA does not seem to support an unbounded item_size query.
        # Workaround:  Set a max (1TB) which is too impractical to download.
        self.size = (
            f"item_size:[{str(min_size.size_in_bytes)} TO "
            f"{str(max_size.size_in_bytes)}]"
        )
        media_type = f"mediatype:{media_type}"
        search_terms = [
            x
            for x in [media_type, self.size, self.title, self.subject]
            if x is not None
        ]
        self.query = " AND ".join(search_terms)
        logger.info(self.query)

    def search_items(self):
        logger.info("Searching...")
        # search_items yields, so we want to yield from it rather than return
        yield from session.search_items(self.query)  # pragma: no cover


def search_pipeline(args: argparse.Namespace):  # pragma: no cover
    """
    Given `title`, `media_type` and `min_size`,
    search Internet Archive for items matching the title.
    """

    search = ArchiveSearch(
        title=args.title,
        media_type=args.media_type,
        min_size=Size(size=args.min_size),
        max_size=Size(size=args.max_size),
        subject=args.subject,
        query_all=args.query_all,
    )

    try:
        items = search.search_items()
        # yaml separator
        # TODO: account for JSON output
        print("---")

        while True:
            try:
                item = session.get_item(next(items)["identifier"])
                if not item.item_size or item.metadata["title"] is None:
                    logger.info(
                        f"Skipping item with identifier \
                                '{item.identifier}' and size '{item.item_size}'"
                    )
                    continue
                # By default, output is yaml
                print(ArchiveItem(item).output)

            except StopIteration:
                logger.info("No more results.")
                break

    # IF control-c is pressed, exit the loop gracefully
    except KeyboardInterrupt:
        print("\r", end="")
        logger.info("Exiting due to user requested stop...")
        exit()


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

    search_pipeline(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
