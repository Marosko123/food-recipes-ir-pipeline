"""Tests for Lucene indexer."""
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock lucene and lupyne BEFORE importing the module
sys.modules['lucene'] = MagicMock()
sys.modules['lupyne'] = MagicMock()
sys.modules['lupyne.engine'] = MagicMock()
sys.modules['org.apache.lucene.search.similarities'] = MagicMock()
sys.modules['org.apache.lucene.document'] = MagicMock()
sys.modules['org.apache.lucene.store'] = MagicMock()
sys.modules['org.apache.lucene.index'] = MagicMock()
sys.modules['org.apache.lucene.analysis.standard'] = MagicMock()
sys.modules['java.nio.file'] = MagicMock()

# Now we can import the module
from indexer.lucene_indexer import LupyneRecipeIndexer

class TestLupyneIndexer(unittest.TestCase):
    """Test LupyneRecipeIndexer helper methods."""

    def setUp(self):
        # Mock __init__ to avoid JVM init and file checks
        with patch.object(LupyneRecipeIndexer, '__init__', return_value=None):
            self.indexer = LupyneRecipeIndexer("dummy_input", "dummy_output")
            # Initialize stats manually since __init__ is skipped
            self.indexer.stats = {
                'total_docs': 0,
                'docs_with_wiki': 0,
                'total_wiki_links': 0
            }

    def test_normalize_ingredients(self):
        """Test ingredient normalization."""
        ingredients = [" Chicken ", "Salt", "", "  Black Pepper  "]
        expected = ["chicken", "salt", "black pepper"]
        result = self.indexer._normalize_ingredients(ingredients)
        self.assertEqual(result, expected)

    def test_extract_wiki_abstracts(self):
        """Test wiki abstract extraction."""
        recipe = {
            "wiki_links": [
                {"abstract": "Abstract 1"},
                {"abstract": "  Abstract 2  "},
                {"abstract": ""}
            ]
        }
        expected = "Abstract 1 Abstract 2"
        result = self.indexer._extract_wiki_abstracts(recipe)
        self.assertEqual(result, expected)
        self.assertEqual(self.indexer.stats['total_wiki_links'], 3)
        self.assertEqual(self.indexer.stats['docs_with_wiki'], 1)

    def test_prepare_document_fields(self):
        """Test document field preparation."""
        recipe = {
            "id": "123",
            "url": "http://example.com",
            "title": "Test Recipe",
            "ingredients": ["Chicken", "Salt"],
            "instructions": ["Cook it."],
            "times": {"total": 30, "prep": 10, "cook": 20},
            "cuisine": ["Italian"],
            "wiki_links": [{"abstract": "Wiki info"}]
        }
        
        fields = self.indexer._prepare_document_fields(recipe)
        
        self.assertEqual(fields['docId'], "123")
        self.assertEqual(fields['title_text'], "Test Recipe")
        self.assertEqual(fields['ingredients_text'], "Chicken Salt")
        self.assertEqual(fields['instructions_text'], "Cook it.")
        self.assertEqual(fields['wiki_abstracts'], "Wiki info")
        self.assertEqual(fields['total_minutes'], 30)
        self.assertEqual(fields['ingredients_kw'], ["chicken", "salt"])
        self.assertEqual(fields['cuisine_kw'], ["Italian"])

if __name__ == '__main__':
    unittest.main()

