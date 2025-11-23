"""Tests for search functionality."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path
import json

# Add parent directory to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from search_cli.run import RobustRecipeSearcher

class TestRobustSearcher(unittest.TestCase):
    """Test RobustRecipeSearcher (TF-IDF/BM25 on TSV index)."""

    def setUp(self):
        """Create a temporary TSV index."""
        self.test_dir = tempfile.mkdtemp()
        self.index_dir = Path(self.test_dir)
        
        # Create dummy index files
        # 1. terms.tsv: term -> df, idf
        with open(self.index_dir / "terms.tsv", "w") as f:
            f.write("term\tdf\tidf\n")
            f.write("chicken\t2\t0.5\n")
            f.write("pasta\t1\t1.0\n")
            f.write("soup\t1\t1.0\n")
            f.write("tomato\t1\t1.0\n")

        # 2. postings.tsv: term -> field, docId, tf
        with open(self.index_dir / "postings.tsv", "w") as f:
            f.write("term\tfield\tdocId\ttf\n")
            # Doc 1: Chicken Pasta
            f.write("chicken\ttitle\t1\t1\n")
            f.write("pasta\ttitle\t1\t1\n")
            f.write("tomato\tingredients\t1\t1\n")
            # Doc 2: Chicken Soup
            f.write("chicken\ttitle\t2\t1\n")
            f.write("soup\ttitle\t2\t1\n")

        # 3. docmeta.tsv: docId -> url, title, lengths...
        with open(self.index_dir / "docmeta.tsv", "w") as f:
            f.write("docId\turl\ttitle\tlen_title\tlen_ing\tlen_instr\n")
            f.write("1\thttp://food.com/1\tChicken Pasta\t2\t5\t10\n")
            f.write("2\thttp://food.com/2\tChicken Soup\t2\t5\t10\n")
            
        # Mock recipes.jsonl for filtering
        self.recipes_file = Path(self.test_dir) / "recipes.jsonl"
        with open(self.recipes_file, "w") as f:
            # Recipe 1
            f.write(json.dumps({
                "id": "1",
                "title": "Chicken Pasta",
                "times": {"total": 30, "prep": 10, "cook": 20},
                "cuisine": ["Italian"],
                "ingredients": ["chicken", "pasta", "tomato"]
            }) + "\n")
            # Recipe 2
            f.write(json.dumps({
                "id": "2",
                "title": "Chicken Soup",
                "times": {"total": 60, "prep": 20, "cook": 40},
                "cuisine": ["American"],
                "ingredients": ["chicken", "water", "salt"]
            }) + "\n")

        # Initialize searcher
        # We need to patch the path to recipes.jsonl inside the class or mock it
        # For now, we'll rely on the searcher finding the index, but filtering might fail if it looks for hardcoded path
        # Let's patch _load_recipes_batch or _get_recipe_data if needed.
        # Actually, RobustRecipeSearcher has hardcoded paths. We should probably make it configurable or patch it.
        
        self.searcher = RobustRecipeSearcher(str(self.index_dir))
        
        # Monkey patch _get_recipe_data to use our local file logic
        original_get_recipe = self.searcher._get_recipe_data
        
        def mock_get_recipe_data(doc_id):
            with open(self.recipes_file, 'r') as f:
                for line in f:
                    r = json.loads(line)
                    if r['id'] == doc_id:
                        return r
            return None
            
        self.searcher._get_recipe_data = mock_get_recipe_data

    def tearDown(self):
        """Cleanup."""
        shutil.rmtree(self.test_dir)

    def test_basic_search_tfidf(self):
        """Test basic TF-IDF search."""
        results = self.searcher.search_tfidf("chicken", k=10)
        self.assertEqual(len(results), 2)
        # Both have "chicken" in title, same TF, same IDF. Should be similar scores.
        ids = sorted([r[0] for r in results])
        self.assertEqual(ids, ["1", "2"])

    def test_search_unique_term(self):
        """Test search for term only in one doc."""
        results = self.searcher.search_tfidf("pasta", k=10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "1")

    def test_filter_time(self):
        """Test time filtering."""
        # Search "chicken" but filter max_total_minutes=45
        # Doc 1 is 30 mins, Doc 2 is 60 mins. Should only get Doc 1.
        filters = {"max_total_minutes": 45}
        results = self.searcher.search_tfidf("chicken", k=10, filters=filters)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "1")

    def test_filter_cuisine(self):
        """Test cuisine filtering."""
        # Search "chicken" with cuisine "American" -> Doc 2
        filters = {"cuisine": ["American"]}
        results = self.searcher.search_tfidf("chicken", k=10, filters=filters)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "2")

    def test_bm25_search(self):
        """Test BM25 search."""
        results = self.searcher.search_bm25("chicken", k=10)
        self.assertEqual(len(results), 2)

if __name__ == '__main__':
    unittest.main()
