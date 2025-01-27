import pytest
import yaml

from anything_finder.iaaf_types import Size
from anything_finder.main import ArchiveItem, ArchiveSearch


class Mock(object):
    pass


def test_size():
    assert Size(size=1).size_in_bytes == 1
    assert Size(size="1GB").size_in_bytes == 1073741824
    assert Size(size="1gB").size_in_bytes == 1073741824
    assert Size(size="1MB").size_in_bytes == 1048576
    assert Size(size="1mb").size_in_bytes == 1048576
    assert Size(size=1111111).size_in_bytes == 1111111


@pytest.mark.parametrize("bad_input", ["-1", "100%", "1.5KB", None, "", "brrrrrrrrrrr"])
def test_size_bad(bad_input):
    # While apparently repetitive, this tests that an exception is raised both
    # on instantiation and on the size_in_bytes property.
    # (Which is implied, but tested for paranoia.)
    with pytest.raises(ValueError):
        Size(size=bad_input)
    with pytest.raises(ValueError):
        Size(size=bad_input).size_in_bytes


def test_archive_search():
    search = ArchiveSearch(title="Kool and the gang", media_type="audio")
    assert (
        search.query
        == 'mediatype:audio AND item_size:[0 TO 1000000000000] AND title:"Kool and the gang"'  # noqa: E501
    )
    search = ArchiveSearch(
        title="Parliment Funkadelic",
        media_type="audio",
    )
    assert (
        search.query
        == 'mediatype:audio AND item_size:[0 TO 1000000000000] AND title:"Parliment Funkadelic"'  # noqa: E501
    )
    search = ArchiveSearch(
        title="George Clinton", media_type="audio", subject="Funk music"
    )
    assert (
        search.query
        == 'mediatype:audio AND item_size:[0 TO 1000000000000] AND title:"George Clinton" AND subject:"Funk music"'  # noqa: E501
    )


def test_archive_search_query_all():
    search = ArchiveSearch(
        title="Curtis Mayfield - Pusherman", media_type="audio", query_all=True
    )
    assert (
        search.query
        == "mediatype:audio AND item_size:[0 TO 1000000000000] AND (Curtis Mayfield - Pusherman)"  # noqa: E501
    )


def test_output():
    ## For these tests, we only need title, item_size, and url.
    # Metadata is a required parameter.
    item = Mock()
    item.metadata = {"title": "Cameo - Word Up", "identifier": "Mock"}
    item.item_size = "12345"
    item.url = "https://example.org/mock"

    output = ArchiveItem(item).output
    assert output == yaml.dump([ArchiveItem(item).dict], sort_keys=False)

    item.metadata = {"title": "Cameo - Word Up: Colon Edition", "identifier": "Mock"}
    output = ArchiveItem(item).output
    assert ArchiveItem(item).dict["title"] == "Cameo - Word Up: Colon Edition"
    # Ensure that a colon-ified string gets properly formatted and doesn't cause havoc.
    assert output.splitlines()[0] == "- title: 'Cameo - Word Up: Colon Edition'"
