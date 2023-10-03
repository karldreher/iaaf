import internetarchive as ia
import argparse
import time
import sys

session = ia.get_session()


class ArchiveItem():
    def __init__(self, item):
        self.item = item
        self.metadata = item.metadata
        self.title = item.metadata['title']
        self.item_size = item.item_size
    def __repr__(self):
        return self.metadata['identifier']
    def download(self):
        self.item.download()
    def download_url(self):
        self.item.download(dry_run=True)

class ArchiveSearch():
    def __init__(self, subject, title_match=False):
        self.subject = f'subject:"{subject}"'
        self.title_match = f'title:"{subject}"' if title_match is True else None
        media_type = 'mediatype:audio'
        search_terms = filter(lambda x: x is not None, [media_type,self.subject,self.title_match])
        self.query = ' AND '.join(search_terms)
    def search_items(self):
        # search_items yields, so we want to yield from it rather than return
        yield from session.search_items(self.query)


def parse_size(size):
    # parse size in bytes, or MB, or GB.  Return size in bytes.
    size = size.upper()
    if size[-2:] == 'MB':
        return int(size[:-2]) * 1024 * 1024
    elif size[-2:] == 'GB':
        return int(size[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size)

def search_pipeline(subject, min_size,title_match):
     # search for items
    search = ArchiveSearch(subject,title_match=title_match)
    # IF control-c is pressed, exit the loop gracefully
    try:
        print("Searching...")
        items=search.search_items()
        while True:
            try:
                item = next(items)    
                g = session.get_item(item['identifier'])
                n = ArchiveItem(g)
                # This is implemented here because the item_size query does not work as expected.  This could be a bug on the IA side. 
                # We would typically expect that the search 'item_size:[1000 TO null]' to work, but it does not.
                if n.item_size < min_size:
                    continue
                #csv.append([g.metadata['identifier'],g.metadata['title'],(f"{(size / 1024 / 1024):.2f} MB")])
                print(n.title)
                print("\t",f"http://archive.org/details/{n.metadata['identifier']}")
                print("\t",n.metadata['mediatype'])
                print("\t",n.item_size)
            except StopIteration:
                print("No more results.")
                break

    except KeyboardInterrupt:
        print("\r", end="")
        print("Exiting...")
        exit()


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('subject', help='subject to search for')
    argparser.add_argument('--min_size', '--min-size', type=str, default="0MB", help='Minimum size of item to search for.  Supports expressions in MB or GB, like 1MB or 1GB')
    argparser.add_argument('--title_match', '--title-match', action='store_true', default=False, help='Use provided subject to search subject AND title.')
    args = argparser.parse_args()
    size = parse_size(args.min_size)
    
    search_pipeline(subject=args.subject, min_size=size, title_match=args.title_match)

if __name__=='__main__':
    sys.exit(main())