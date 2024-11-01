import argparse
import logging
import sys
import json
from internetarchive import get_session, configure, Item
import yaml

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
        subject: str = None
    ):
        # Title may not default to None, as it is required.
        self.title = f'title:"{title}"'
        self.subject = f'subject:"{subject}"' if subject else None
        # IA does not seem to support an unbounded item_size query.
        # Workaround:  Set a max (1TB) which is too impractical to download.
        self.size = f"item_size:[{str(min_size.size_in_bytes)} TO 1000000000000]"
        media_type = f"mediatype:{media_type}"
        search_terms = filter(
            lambda x: x is not None, [media_type, self.size, self.title, self.subject]
        )
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
        subject=args.subject,
    )

    try:
        items = search.search_items()
        # yaml separator
        # TODO: account for JSON output
        print("---")

        while True:
            try:
                item = session.get_item(next(items)["identifier"])
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
