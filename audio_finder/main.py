import argparse
import logging
import sys

import internetarchive as ia
import yaml

session = ia.get_session()
logger = logging.getLogger(__name__)


class ArchiveItem:
    def __init__(self, item):
        self.item = item
        self.metadata = item.metadata
        self.title = item.metadata["title"]
        self.item_size = item.item_size
        self.url = f"http://archive.org/details/{self}"

    def __repr__(self):
        return self.metadata["identifier"]

    def download(self):
        self.item.download()

    def download_url(self):
        self.item.download(dry_run=True)


class ArchiveSearch:
    def __init__(self, title, subject=None):
        self.title = f'title:"{title}"'
        self.subject = f'subject:"{subject}"' if subject else None
        media_type = "mediatype:audio"
        search_terms = filter(
            lambda x: x is not None, [media_type, self.title, self.subject]
        )
        self.query = " AND ".join(search_terms)

    def search_items(self):
        # search_items yields, so we want to yield from it rather than return
        yield from session.search_items(self.query)


class Output:
    def __init__(self, item: ArchiveItem):
        self.dict = {item.title: [{"size": item.item_size}, {"url": item.url}]}
        self.yaml = yaml.dump(self.dict)


def parse_size(size):
    """
    Parse size in bytes, or MB, or GB.  Return size in bytes.
    """
    size = size.upper()
    if size[-2:] == "MB":
        return int(size[:-2]) * 1024 * 1024
    elif size[-2:] == "GB":
        return int(size[:-2]) * 1024 * 1024 * 1024
    return int(size)


def search_pipeline(args: argparse.Namespace):
    """
    Given `title` and `min_size`, search Internet Archive for audio matching the title.
    """
    min_size = parse_size(args.min_size)
    search = ArchiveSearch(title=args.title, subject=args.subject)

    # IF control-c is pressed, exit the loop gracefully
    try:
        logger.info("Searching...")
        items = search.search_items()
        while True:
            try:
                item = next(items)
                g = session.get_item(item["identifier"])
                n = ArchiveItem(g)
                # This is implemented here because the item_size query does.  
                # not seem to work on the IA side.
                # It is expected that the search 'item_size:[1000 TO null]' can work, 
                # but it does not.
                if n.item_size < min_size:
                    continue

                # By default, output is yaml
                print("---")
                print(Output(n).yaml)
            except StopIteration:
                logger.info("No more results.")
                break
    except KeyboardInterrupt:
        print("\r", end="")
        logger.info("Exiting due to user requested stop...")
        exit()


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--config",
        "--configure",
        action="store_true",
        help="Configure authentication to Internet Archive.",
    )
    argparser.add_argument(
        "title",
        nargs="?" if "--config" in sys.argv else None,
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

    args = argparser.parse_args()
    # Debug catches a lot of lower level stuff from IA, which we don't need right now.
    # In the future, may consider additional verbosity levels.
    logging.basicConfig(level=(logging.INFO if args.verbose else logging.WARN))

    if args.config:
        print("Enter your Internet Archive credentials.")
        ia.configure()
        exit()
    search_pipeline(args)


if __name__ == "__main__":
    sys.exit(main())
