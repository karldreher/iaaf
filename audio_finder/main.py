import internetarchive as ia
import argparse
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
    def __init__(self, title, subject=None):
        self.title = f'title:"{title}"'
        self.subject = f'subject:"{subject}"' if subject else None
        media_type = 'mediatype:audio'
        search_terms = filter(lambda x: x is not None, [media_type,self.title,self.subject])
        self.query = ' AND '.join(search_terms)
    def search_items(self):
        # search_items yields, so we want to yield from it rather than return
        yield from session.search_items(self.query)


def parse_size(size):
    '''
    Parse size in bytes, or MB, or GB.  Return size in bytes.
    '''
    size = size.upper()
    if size[-2:] == 'MB':
        return int(size[:-2]) * 1024 * 1024
    elif size[-2:] == 'GB':
        return int(size[:-2]) * 1024 * 1024 * 1024
    return int(size)

def search_pipeline(title, min_size, subject):
    '''
    Given `title` and `min_size`, search Internet Archive for audio matching the title.
    '''
    search = ArchiveSearch(title=title,subject=subject)
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
    argparser.add_argument('title', help='Title to search for.  Always required.')
    argparser.add_argument('--subject', type=str, default=None, help='Optional subject to search for.')
    argparser.add_argument('--min_size', '--min-size', type=str, default="0MB", help='Minimum size of item to search for.  Supports expressions in MB or GB, like 1MB or 1GB')
    args = argparser.parse_args()
    size = parse_size(args.min_size)
    
    search_pipeline(title=args.title, min_size=size, subject=args.subject)

if __name__=='__main__':
    sys.exit(main())