import argparse
import logging
import sys

import internetarchive as ia
import yaml

session = ia.get_session()
logger = logging.getLogger(__name__)


class ArchiveItem:
    def __init__(self, item: ia.item.Item):
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
    def __init__(self, title: str, min_size: int = 0, subject: str = None):
        self.title = f'title:"{title}"'
        self.subject = f'subject:"{subject}"' if subject else None
        # IA does not seem to support an unbounded item_size query.
        # Workaround:  Set a max (1TB) which is too impractical to download.
        self.size = f"item_size:[{str(min_size)} TO 1000000000000]"
        media_type = "mediatype:audio"
        search_terms = filter(
            lambda x: x is not None, [media_type, self.size, self.title, self.subject]
        )
        self.query = " AND ".join(search_terms)

    def search_items(self):
        # search_items yields, so we want to yield from it rather than return
        yield from session.search_items(self.query)  # pragma: no cover


class Output:
    def __init__(self, item: ArchiveItem):
        self.dict = {"title": item.title, "size": item.item_size, "url": item.url}
        self.yaml = yaml.dump([self.dict], sort_keys=False)


def parse_size(size):
    """
    Parse size in bytes, or MB, or GB.  Return size in bytes.
    """
    if isinstance(size, int):
        return size 
    if isinstance(size, str) and (size[-2:] == "MB" or size[-2:] == "GB"):
        size = size.upper()
        if size[-2:] == "MB":
            return int(size[:-2]) * 1024 * 1024
        elif size[-2:] == "GB":
            return int(size[:-2]) * 1024 * 1024 * 1024
        return int(size)
    else:
        raise ValueError("Size must be in bytes(int), MB, or GB.")



def search_pipeline(args: argparse.Namespace):  # pragma: no cover
    """
    Given `title` and `min_size`, search Internet Archive for audio matching the title.
    """
    min_size = parse_size(args.min_size)
    search = ArchiveSearch(title=args.title, min_size=min_size, subject=args.subject)

    # IF control-c is pressed, exit the loop gracefully
    try:
        logger.info("Searching...")
        items = search.search_items()
        logger.info(search.query)
        # yaml separator
        print("---")

        while True:
            try:
                item = next(items)
                g = session.get_item(item["identifier"])
                n = ArchiveItem(g)

                # By default, output is yaml
                print(Output(n).yaml)
            except StopIteration:
                logger.info("No more results.")
                break
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
        help="Configure authentication to Internet Archive.",
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
        ia.configure()
        exit()
    if args.version:
        from audio_finder import __version__
        print(__version__)
        exit()
    search_pipeline(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
