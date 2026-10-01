import pytest
from click.testing import CliRunner

from anything_finder import __version__, cli


@pytest.fixture
def runner():
    return CliRunner()


def test_version(runner):
    result = runner.invoke(cli.main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_search_requires_media_type(runner):
    result = runner.invoke(cli.main, ["search", "foo"])
    assert result.exit_code == 2
    assert "--media-type" in result.output


def test_search_requires_title(runner):
    result = runner.invoke(cli.main, ["search", "--type", "audio"])
    assert result.exit_code == 2


def test_search_invalid_media_type(runner):
    result = runner.invoke(cli.main, ["search", "foo", "--type", "bogus"])
    assert result.exit_code == 2


def test_search_invalid_size(runner):
    result = runner.invoke(
        cli.main, ["search", "foo", "--type", "audio", "--min-size", "5XB"]
    )
    assert result.exit_code == 2
    assert "Size must be" in result.output


@pytest.mark.parametrize("flag", ["--media-type", "--media_type", "--type"])
def test_search_passes_options(runner, monkeypatch, flag):
    calls = []
    monkeypatch.setattr(cli, "search_pipeline", lambda **kw: calls.append(kw))
    result = runner.invoke(
        cli.main,
        ["search", "foo", flag, "audio", "--subject", "jazz", "--query_all"],
    )
    assert result.exit_code == 0
    assert calls == [
        {
            "title": "foo",
            "media_type": "audio",
            "min_size": "0MB",
            "max_size": "1000GB",
            "subject": "jazz",
            "query_all": True,
        }
    ]


def test_configure(runner, monkeypatch):
    called = []
    monkeypatch.setattr(cli, "ia_configure", lambda: called.append(True))
    result = runner.invoke(cli.main, ["configure"])
    assert result.exit_code == 0
    assert called == [True]
    assert "Enter your Internet Archive credentials." in result.output
