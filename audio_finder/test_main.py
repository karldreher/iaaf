from audio_finder.main import ArchiveSearch,parse_size

def test_parse_size():
    assert parse_size("1GB") == 1073741824
    assert parse_size("1MB") == 1048576

def test_archive_search():
    search = ArchiveSearch("Kool and the gang")
    assert search.query == 'mediatype:audio AND subject:"Kool and the gang"'
    search = ArchiveSearch(subject="Parliment Funkadelic", title_match=True)
    assert search.query == 'mediatype:audio AND subject:"Parliment Funkadelic" AND title:"Parliment Funkadelic"'
