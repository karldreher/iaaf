import json
import signal
from unittest.mock import MagicMock

import pytest
import yaml

from anything_finder import search as search_module
from anything_finder.iaaf_types import Size
from anything_finder.search import ArchiveItem, ArchiveSearch


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


def test_archive_search_max_and_min_size():
    search = ArchiveSearch(
        title="James Brown",
        media_type="audio",
        min_size=Size(size="10MB"),
        max_size=Size(size="100MB"),
    )
    assert (
        search.query
        == 'mediatype:audio AND item_size:[10485760 TO 104857600] AND title:"James Brown"'  # noqa: E501
    )


def test_archive_search_query_all():
    search = ArchiveSearch(
        title="Curtis Mayfield - Pusherman", media_type="audio", query_all=True
    )
    assert (
        search.query
        == "mediatype:audio AND item_size:[0 TO 1000000000000] AND (Curtis Mayfield - Pusherman)"  # noqa: E501
    )


def _mock_item():
    item = MagicMock()
    item.metadata = {"title": "Cameo - Word Up", "identifier": "Mock"}
    item.item_size = "12345"
    return item


def test_render_json():
    archive_item = ArchiveItem(_mock_item())
    assert json.loads(archive_item.render("json")) == archive_item.dict


def test_render_yaml_matches_output():
    archive_item = ArchiveItem(_mock_item())
    assert archive_item.render("yaml") == archive_item.output


def test_render_invalid_format():
    with pytest.raises(ValueError):
        ArchiveItem(_mock_item()).render("xml")


def test_output():
    ## For these tests, we only need title, item_size, and url.
    # Metadata is a required parameter.
    item = MagicMock()
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


class _FakeSearch:
    def __init__(self, identifiers):
        self.identifiers = identifiers

    def search_items(self):
        yield from ({"identifier": i} for i in self.identifiers)


def _run_pipeline(monkeypatch, identifiers, output_format):
    def get_item(identifier):
        item = MagicMock()
        item.metadata = {"title": f"Title {identifier}", "identifier": identifier}
        item.item_size = 100
        return item

    monkeypatch.setattr(search_module, "session", MagicMock(get_item=get_item))
    monkeypatch.setattr(
        search_module, "ArchiveSearch", lambda **kw: _FakeSearch(identifiers)
    )
    search_module.search_pipeline(
        title="x", media_type="audio", output_format=output_format
    )


@pytest.mark.parametrize("identifiers", [[], ["a"], ["a", "b"]])
def test_pipeline_json_is_valid_array(monkeypatch, capsys, identifiers):
    _run_pipeline(monkeypatch, identifiers, "json")
    parsed = json.loads(capsys.readouterr().out)
    assert [entry["title"] for entry in parsed] == [f"Title {i}" for i in identifiers]


def test_pipeline_yaml_unchanged(monkeypatch, capsys):
    _run_pipeline(monkeypatch, ["a"], "yaml")
    out = capsys.readouterr().out
    assert out.startswith("---\n")
    assert yaml.safe_load(out)[0]["title"] == "Title a"


def _run_pipeline_interrupted(monkeypatch, output_format):
    """Interrupt on the second item; get_item swallows nothing, the flag stops us."""
    calls = []

    def get_item(identifier):
        calls.append(identifier)
        if len(calls) == 2:
            signal.raise_signal(signal.SIGINT)
        item = MagicMock()
        item.metadata = {"title": f"Title {identifier}", "identifier": identifier}
        item.item_size = 100
        return item

    monkeypatch.setattr(search_module, "session", MagicMock(get_item=get_item))
    monkeypatch.setattr(
        search_module, "ArchiveSearch", lambda **kw: _FakeSearch(["a", "b", "c"])
    )
    previous = signal.getsignal(signal.SIGINT)
    search_module.search_pipeline(
        title="x", media_type="audio", output_format=output_format
    )
    assert signal.getsignal(signal.SIGINT) is previous
    return calls


def test_pipeline_json_stops_on_sigint(monkeypatch, capsys):
    calls = _run_pipeline_interrupted(monkeypatch, "json")
    parsed = json.loads(capsys.readouterr().out)
    # The interrupted item is dropped and nothing is fetched afterward.
    assert [entry["title"] for entry in parsed] == ["Title a"]
    assert calls == ["a", "b"]


def test_pipeline_yaml_stops_on_sigint(monkeypatch, capsys):
    _run_pipeline_interrupted(monkeypatch, "yaml")
    out = capsys.readouterr().out
    assert [entry["title"] for entry in yaml.safe_load(out)] == ["Title a"]
