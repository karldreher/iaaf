from audio_finder.main import ArchiveItem, ArchiveSearch, Output, parse_size, yaml


class Mock(object):
    pass


def test_parse_size():
    assert parse_size("1GB") == 1073741824
    assert parse_size("1MB") == 1048576


def test_archive_search():
    search = ArchiveSearch(title="Kool and the gang")
    assert (
        search.query
        == 'mediatype:audio AND item_size:[0 TO 1000000000000] AND title:"Kool and the gang"'  # noqa: E501
    )
    search = ArchiveSearch(title="Parliment Funkadelic")
    assert (
        search.query
        == 'mediatype:audio AND item_size:[0 TO 1000000000000] AND title:"Parliment Funkadelic"'  # noqa: E501
    )
    search = ArchiveSearch(title="George Clinton", subject="Funk music")
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
