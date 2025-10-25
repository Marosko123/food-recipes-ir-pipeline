"""Tests for output formatting."""
from search_cli.formatters import clean_wiki_abstract


def test_wiki_cleaning():
    """Test Wikipedia abstract cleaning."""
    dirty = "Chocolate (, ; ) is food|editor=John"
    clean = clean_wiki_abstract(dirty, max_len=50)
    assert '(, ; )' not in clean
    assert '|editor=' not in clean
    assert len(clean) <= 50


def test_truncation():
    """Test abstract truncation."""
    long_text = "A" * 200
    result = clean_wiki_abstract(long_text, max_len=100)
    assert len(result) <= 103  # 100 + '...'
    assert result.endswith('...')
