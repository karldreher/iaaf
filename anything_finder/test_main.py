import pytest

from anything_finder.main import ArchiveItem, ArchiveSearch, Output, parse_size, yaml
from anything_finder.iaaf_types import Size

class Mock(object):
    pass


def test_parse_size():
    assert Size(size=1).size_in_bytes == 1
    assert Size(size="1GB").size_in_bytes == 1073741824
    assert Size(size="1gB").size_in_bytes == 1073741824
    assert Size(size="1MB").size_in_bytes == 1048576
    assert Size(size="1mb").size_in_bytes == 1048576
    assert Size(size=1111111).size_in_bytes == 1111111


@pytest.mark.parametrize("bad_input", ["-1", "100%", "1.5KB", None, "", "brrrrrrrrrrr"])
def test_parse_size_bad(bad_input):
    with pytest.raises(ValueError):
        # TODO: field validator should remove size_in_bytes from this test (i think)
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


def test_output():
    ## For these tests, we only need title, item_size, and url.
    # Metadata is a required parameter.
    item = Mock()
    item.metadata = {"title": "Cameo - Word Up", "identifier": "Mock"}
    item.item_size = "12345"
    item.url = "https://example.org/mock"
    output = Output(ArchiveItem(item))
    assert output.yaml == yaml.dump([output.dict], sort_keys=False)

    item.metadata = {"title": "Cameo - Word Up: Colon Edition", "identifier": "Mock"}
    output = Output(ArchiveItem(item))
    assert output.dict["title"] == "Cameo - Word Up: Colon Edition"
    # Ensure that a colon-ified string gets properly formatted and doesn't cause havoc.
    assert output.yaml.splitlines()[0] == "- title: 'Cameo - Word Up: Colon Edition'"
