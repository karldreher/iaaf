from audio_finder.main import ArchiveSearch, parse_size


def test_parse_size():
    assert parse_size("1GB") == 1073741824
    assert parse_size("1MB") == 1048576


def test_archive_search():
    search = ArchiveSearch(title="Kool and the gang")
    assert search.query == 'mediatype:audio AND title:"Kool and the gang"'
    search = ArchiveSearch(title="Parliment Funkadelic")
    assert search.query == 'mediatype:audio AND title:"Parliment Funkadelic"'
    search = ArchiveSearch(title="George Clinton", subject="Funk music")
    assert (
        search.query
        == 'mediatype:audio AND title:"George Clinton" AND subject:"Funk music"'
    )
