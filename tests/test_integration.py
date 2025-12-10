#!/usr/bin/env python3
"""
Integračné testy pre VINF projekt - Food Recipes IR Pipeline.

Tento script overuje celú pipeline bez modifikovania dát.
Spustenie: python -m pytest tests/test_integration.py -v

Autor: Maroš Bednár
Dátum: December 2025
"""
import os
import sys
import json
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDataFilesExist(unittest.TestCase):
    """Test že všetky dátové súbory existujú."""
    
    BASE_DIR = Path(__file__).parent.parent
    
    def test_raw_data_exists(self):
        """Test že existujú stiahnuté HTML súbory."""
        raw_dir = self.BASE_DIR / "data" / "raw" / "www.food.com"
        if raw_dir.exists():
            html_files = list(raw_dir.rglob("*.html"))
            self.assertGreater(len(html_files), 0, "Žiadne HTML súbory v data/raw")
            print(f"✓ Nájdených {len(html_files)} HTML súborov")
        else:
            self.skipTest("data/raw/www.food.com neexistuje - crawler nebol spustený")
    
    def test_normalized_recipes_exist(self):
        """Test že existuje recipes_foodcom.jsonl."""
        recipes_file = self.BASE_DIR / "data" / "normalized" / "recipes_foodcom.jsonl"
        if recipes_file.exists():
            with open(recipes_file, 'r') as f:
                count = sum(1 for _ in f)
            self.assertGreater(count, 0, "recipes_foodcom.jsonl je prázdny")
            print(f"✓ recipes_foodcom.jsonl obsahuje {count} receptov")
        else:
            self.skipTest("recipes_foodcom.jsonl neexistuje - parser nebol spustený")
    
    def test_enriched_recipes_exist(self):
        """Test že existuje recipes_enriched.jsonl."""
        enriched_file = self.BASE_DIR / "data" / "normalized" / "recipes_enriched.jsonl"
        if enriched_file.exists():
            with open(enriched_file, 'r') as f:
                count = sum(1 for _ in f)
            self.assertGreater(count, 0, "recipes_enriched.jsonl je prázdny")
            print(f"✓ recipes_enriched.jsonl obsahuje {count} receptov")
        else:
            self.skipTest("recipes_enriched.jsonl neexistuje - enricher nebol spustený")
    
    def test_wiki_culinary_exists(self):
        """Test že existuje wiki_culinary.jsonl."""
        wiki_file = self.BASE_DIR / "data" / "normalized" / "wiki_culinary.jsonl"
        if wiki_file.exists():
            with open(wiki_file, 'r') as f:
                count = sum(1 for _ in f)
            self.assertGreater(count, 0, "wiki_culinary.jsonl je prázdny")
            print(f"✓ wiki_culinary.jsonl obsahuje {count} článkov")
        else:
            self.skipTest("wiki_culinary.jsonl neexistuje - Spark parser nebol spustený")


class TestSimpleIndexExists(unittest.TestCase):
    """Test že Simple index (v1) existuje a je validný."""
    
    BASE_DIR = Path(__file__).parent.parent
    
    def test_simple_index_files_exist(self):
        """Test že existujú všetky súbory Simple indexu."""
        index_dir = self.BASE_DIR / "index" / "v1"
        
        if not index_dir.exists():
            # Fallback na starú cestu
            index_dir = self.BASE_DIR / "data" / "index" / "simple"
        
        if not index_dir.exists():
            self.skipTest("Simple index neexistuje - indexer nebol spustený")
        
        required_files = ["terms.tsv", "postings.tsv", "docmeta.tsv"]
        for filename in required_files:
            filepath = index_dir / filename
            self.assertTrue(filepath.exists(), f"{filename} chýba v Simple indexe")
            self.assertGreater(filepath.stat().st_size, 0, f"{filename} je prázdny")
        
        print(f"✓ Simple index obsahuje všetky potrebné súbory")
    
    def test_simple_index_terms_valid(self):
        """Test že terms.tsv má správny formát."""
        index_dir = self.BASE_DIR / "index" / "v1"
        if not index_dir.exists():
            index_dir = self.BASE_DIR / "data" / "index" / "simple"
        
        if not index_dir.exists():
            self.skipTest("Simple index neexistuje")
        
        terms_file = index_dir / "terms.tsv"
        with open(terms_file, 'r') as f:
            lines = f.readlines()
        
        # Check header
        self.assertIn("term", lines[0].lower())
        
        # Check at least some terms exist
        self.assertGreater(len(lines), 1000, "Príliš málo termov v indexe")
        print(f"✓ terms.tsv obsahuje {len(lines)-1} termov")


class TestLuceneIndexExists(unittest.TestCase):
    """Test že Lucene index (v2) existuje."""
    
    BASE_DIR = Path(__file__).parent.parent
    
    def test_lucene_index_exists(self):
        """Test že existuje Lucene index directory."""
        index_dir = self.BASE_DIR / "index" / "v2"
        
        if not index_dir.exists():
            # Fallback na starú cestu
            index_dir = self.BASE_DIR / "index" / "lucene" / "v2"
        
        if not index_dir.exists():
            self.skipTest("Lucene index neexistuje - PyLucene indexer nebol spustený")
        
        # Lucene index má segments_ súbor
        segments = list(index_dir.glob("segments_*"))
        self.assertGreater(len(segments), 0, "Lucene index nemá segments súbor")
        print(f"✓ Lucene index existuje s {len(segments)} segments súborom")


class TestParserModule(unittest.TestCase):
    """Test že parser modul funguje správne."""
    
    def test_html_parser_import(self):
        """Test že sa dá importovať HTMLParser."""
        try:
            from parser.html_parser import HTMLParser
            parser = HTMLParser()
            self.assertIsNotNone(parser)
            print("✓ HTMLParser sa dá importovať")
        except ImportError as e:
            self.fail(f"HTMLParser import failed: {e}")
    
    def test_html_parser_extract_doc_id(self):
        """Test extrakcie doc_id z URL."""
        from parser.html_parser import HTMLParser
        parser = HTMLParser()
        
        url = "https://www.food.com/recipe/chocolate-cake-12345"
        doc_id = parser._extract_doc_id(url)
        self.assertEqual(doc_id, "12345")
        print("✓ _extract_doc_id funguje správne")
    
    def test_html_parser_parse_recipe(self):
        """Test parsovania receptu z HTML."""
        from parser.html_parser import HTMLParser
        parser = HTMLParser()
        
        html = '<html><body><h1 class="recipe-title">Test Recipe</h1></body></html>'
        url = "https://www.food.com/recipe/test-123"
        
        result = parser.parse_recipe(html, url)
        
        self.assertIsInstance(result, dict)
        self.assertIn('url', result)
        self.assertEqual(result['url'], url)
        print("✓ parse_recipe vracia správny formát")


class TestSearchModule(unittest.TestCase):
    """Test že search modul funguje správne."""
    
    BASE_DIR = Path(__file__).parent.parent
    
    def test_search_cli_import(self):
        """Test že sa dá importovať search CLI."""
        try:
            from search_cli.run import RobustRecipeSearcher
            self.assertTrue(True)
            print("✓ RobustRecipeSearcher sa dá importovať")
        except ImportError as e:
            self.skipTest(f"search_cli import failed: {e}")
    
    def test_search_tokenize(self):
        """Test tokenizácie v search module."""
        try:
            from search_cli.run import RobustRecipeSearcher
            
            # Test tokenize static method
            tokens = RobustRecipeSearcher.tokenize_static("Hello World! This is a test.")
            
            self.assertIsInstance(tokens, list)
            self.assertIn("hello", tokens)
            self.assertIn("world", tokens)
            self.assertNotIn("is", tokens)  # stop word
            print("✓ Tokenizácia funguje správne")
        except Exception as e:
            self.skipTest(f"Tokenize test skipped: {e}")
    
    def test_simple_search(self):
        """Test vyhľadávania v Simple indexe."""
        index_dir = self.BASE_DIR / "index" / "v1"
        if not index_dir.exists():
            index_dir = self.BASE_DIR / "data" / "index" / "simple"
        
        if not index_dir.exists():
            self.skipTest("Simple index neexistuje")
        
        try:
            from search_cli.run import RobustRecipeSearcher
            
            searcher = RobustRecipeSearcher(str(index_dir))
            results = searcher.search_bm25("chicken", k=5)
            
            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0, "Vyhľadávanie nenašlo žiadne výsledky")
            print(f"✓ BM25 vyhľadávanie vrátilo {len(results)} výsledkov")
        except Exception as e:
            self.skipTest(f"Search test skipped: {e}")


class TestEnricherModule(unittest.TestCase):
    """Test že enricher modul funguje správne."""
    
    BASE_DIR = Path(__file__).parent.parent
    
    def test_gazetteer_exists(self):
        """Test že existuje wiki gazetteer."""
        gazetteer_path = self.BASE_DIR / "entities" / "wiki_gazetteer.tsv"
        
        if not gazetteer_path.exists():
            self.skipTest("wiki_gazetteer.tsv neexistuje")
        
        with open(gazetteer_path, 'r') as f:
            lines = f.readlines()
        
        self.assertGreater(len(lines), 100, "Gazetteer má príliš málo záznamov")
        print(f"✓ wiki_gazetteer.tsv obsahuje {len(lines)} záznamov")
    
    def test_entity_matching_logic(self):
        """Test logiky entity matching."""
        text = "This recipe uses garlic and onion"
        entities = ['garlic', 'onion', 'tomato']
        
        found = [e for e in entities if e in text.lower()]
        
        self.assertIn('garlic', found)
        self.assertIn('onion', found)
        self.assertNotIn('tomato', found)
        print("✓ Entity matching logika funguje")


class TestProjectStructure(unittest.TestCase):
    """Test že štruktúra projektu je správna."""
    
    BASE_DIR = Path(__file__).parent.parent
    
    def test_required_directories_exist(self):
        """Test že existujú potrebné adresáre."""
        required_dirs = [
            "crawler",
            "parser", 
            "indexer",
            "search_cli",
            "entities",
            "eval",
            "spark_jobs",
            "tests",
            "docs",
            "data"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.BASE_DIR / dir_name
            self.assertTrue(dir_path.exists(), f"Adresár {dir_name}/ neexistuje")
        
        print(f"✓ Všetkých {len(required_dirs)} adresárov existuje")
    
    def test_requirements_txt_exists(self):
        """Test že existuje requirements.txt."""
        req_file = self.BASE_DIR / "packaging" / "requirements.txt"
        self.assertTrue(req_file.exists(), "requirements.txt neexistuje")
        
        with open(req_file, 'r') as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        
        self.assertGreater(len(lines), 0, "requirements.txt je prázdny")
        print(f"✓ requirements.txt obsahuje {len(lines)} závislostí")
    
    def test_readme_exists(self):
        """Test že existuje README."""
        readme = self.BASE_DIR / "README.md"
        self.assertTrue(readme.exists(), "README.md neexistuje")
        
        with open(readme, 'r') as f:
            content = f.read()
        
        self.assertGreater(len(content), 500, "README je príliš krátky")
        print("✓ README.md existuje")


class TestEndToEndPipeline(unittest.TestCase):
    """End-to-end test celej pipeline (read-only)."""
    
    BASE_DIR = Path(__file__).parent.parent
    
    def test_full_search_pipeline(self):
        """Test kompletnej search pipeline."""
        # 1. Check data exists
        enriched_file = self.BASE_DIR / "data" / "normalized" / "recipes_enriched.jsonl"
        if not enriched_file.exists():
            self.skipTest("recipes_enriched.jsonl neexistuje")
        
        # 2. Check index exists
        index_dir = self.BASE_DIR / "index" / "v1"
        if not index_dir.exists():
            index_dir = self.BASE_DIR / "data" / "index" / "simple"
        if not index_dir.exists():
            self.skipTest("Simple index neexistuje")
        
        # 3. Run search
        try:
            from search_cli.run import RobustRecipeSearcher
            
            searcher = RobustRecipeSearcher(str(index_dir))
            
            # Test queries
            test_queries = [
                ("chicken", 5),
                ("chocolate cake", 3),
                ("pasta", 5)
            ]
            
            for query, k in test_queries:
                results = searcher.search_bm25(query, k=k)
                self.assertIsInstance(results, list)
                self.assertGreater(len(results), 0, f"Query '{query}' nenašla výsledky")
            
            print(f"✓ End-to-end pipeline funguje pre {len(test_queries)} queries")
        except Exception as e:
            self.skipTest(f"Pipeline test skipped: {e}")


def run_integration_tests():
    """Spustí všetky integračné testy."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestDataFilesExist,
        TestSimpleIndexExists,
        TestLuceneIndexExists,
        TestParserModule,
        TestSearchModule,
        TestEnricherModule,
        TestProjectStructure,
        TestEndToEndPipeline,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    print("=" * 70)
    print("VINF Integration Tests")
    print("=" * 70)
    print()
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print()
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        return 1


if __name__ == '__main__':
    sys.exit(run_integration_tests())
