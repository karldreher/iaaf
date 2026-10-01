import json
import logging

import yaml
from internetarchive import Item, get_session

from anything_finder.iaaf_types import Size

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

    def render(self, format: str) -> str:
        if format == "yaml":
            return yaml.dump([self.dict], sort_keys=False)
        if format == "json":
            return json.dumps(self.dict)
        raise ValueError("Output format must be yaml or json.")

    @property
    def output(self) -> str:
        return self.render("yaml")


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


def search_pipeline(
    title: str,
    media_type: str,
    min_size: str = "0MB",
    max_size: str = "1000GB",
    subject: str | None = None,
    query_all: bool = False,
):  # pragma: no cover
    """
    Given `title`, `media_type` and `min_size`,
    search Internet Archive for items matching the title.
    """

    search = ArchiveSearch(
        title=title,
        media_type=media_type,
        min_size=Size(size=min_size),
        max_size=Size(size=max_size),
        subject=subject,
        query_all=query_all,
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
        return
