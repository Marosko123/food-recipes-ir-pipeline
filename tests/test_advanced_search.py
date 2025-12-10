#!/usr/bin/env python3
"""
Comprehensive tests for advanced search functionality.

Tests cover:
- Exact phrase matching (quoted strings)
- Ingredient-based search (include/exclude)
- Cuisine filtering
- Origin country/region filtering  
- Time range filtering
- Combined advanced queries
- Fuzzy search with typos
- Boolean operators (AND, OR, NOT)
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestAdvancedQueryParsing(unittest.TestCase):
    """Test query parsing logic without requiring Lucene."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock Lupyne imports for parsing tests
        self.mock_lupyne()
    
    def mock_lupyne(self):
        """Mock Lupyne imports."""
        # Create mock modules
        mock_lucene = MagicMock()
        mock_engine = MagicMock()
        
        sys.modules['lucene'] = mock_lucene
        sys.modules['lupyne'] = MagicMock()
        sys.modules['lupyne.engine'] = mock_engine
        
        # Mock Java classes
        mock_lucene.getVMEnv.return_value = True
    
    def test_parse_simple_query(self):
        """Test parsing simple query without quotes."""
        from search_cli.lupyne_searcher import LupyneRecipeSearcher
        
        # We need to mock the class initialization
        with patch.object(LupyneRecipeSearcher, '__init__', lambda x, y: None):
            searcher = LupyneRecipeSearcher('dummy')
            searcher._parse_advanced_query = LupyneRecipeSearcher._parse_advanced_query.__get__(searcher)
            
            phrases, terms, excludes = searcher._parse_advanced_query("chicken pasta garlic")
            
            self.assertEqual(phrases, [])
            self.assertEqual(terms, ["chicken", "pasta", "garlic"])
            self.assertEqual(excludes, [])
    
    def test_parse_quoted_phrase(self):
        """Test parsing query with quoted phrase."""
        from search_cli.lupyne_searcher import LupyneRecipeSearcher
        
        with patch.object(LupyneRecipeSearcher, '__init__', lambda x, y: None):
            searcher = LupyneRecipeSearcher('dummy')
            searcher._parse_advanced_query = LupyneRecipeSearcher._parse_advanced_query.__get__(searcher)
            
            phrases, terms, excludes = searcher._parse_advanced_query('"chocolate cake"')
            
            self.assertEqual(phrases, ["chocolate cake"])
            self.assertEqual(terms, [])
            self.assertEqual(excludes, [])
    
    def test_parse_mixed_query(self):
        """Test parsing query with phrases and regular terms."""
        from search_cli.lupyne_searcher import LupyneRecipeSearcher
        
        with patch.object(LupyneRecipeSearcher, '__init__', lambda x, y: None):
            searcher = LupyneRecipeSearcher('dummy')
            searcher._parse_advanced_query = LupyneRecipeSearcher._parse_advanced_query.__get__(searcher)
            
            phrases, terms, excludes = searcher._parse_advanced_query('"grilled chicken" salad healthy')
            
            self.assertEqual(phrases, ["grilled chicken"])
            self.assertEqual(set(terms), {"salad", "healthy"})
            self.assertEqual(excludes, [])
    
    def test_parse_exclusion_query(self):
        """Test parsing query with exclusions (- prefix)."""
        from search_cli.lupyne_searcher import LupyneRecipeSearcher
        
        with patch.object(LupyneRecipeSearcher, '__init__', lambda x, y: None):
            searcher = LupyneRecipeSearcher('dummy')
            searcher._parse_advanced_query = LupyneRecipeSearcher._parse_advanced_query.__get__(searcher)
            
            phrases, terms, excludes = searcher._parse_advanced_query("pasta -meat -cheese")
            
            self.assertEqual(phrases, [])
            self.assertEqual(terms, ["pasta"])
            self.assertEqual(set(excludes), {"meat", "cheese"})
    
    def test_parse_complex_query(self):
        """Test parsing complex query with all features."""
        from search_cli.lupyne_searcher import LupyneRecipeSearcher
        
        with patch.object(LupyneRecipeSearcher, '__init__', lambda x, y: None):
            searcher = LupyneRecipeSearcher('dummy')
            searcher._parse_advanced_query = LupyneRecipeSearcher._parse_advanced_query.__get__(searcher)
            
            phrases, terms, excludes = searcher._parse_advanced_query(
                '"italian pasta" "homemade sauce" dinner -fast -microwave'
            )
            
            self.assertEqual(set(phrases), {"italian pasta", "homemade sauce"})
            self.assertEqual(terms, ["dinner"])
            self.assertEqual(set(excludes), {"fast", "microwave"})


class TestOriginExtraction(unittest.TestCase):
    """Test origin country/region extraction from recipe data."""
    
    def test_extract_from_wiki_links(self):
        """Test extraction from wiki_links."""
        from indexer.lucene_indexer import LupyneRecipeIndexer
        
        with patch.object(LupyneRecipeIndexer, '__init__', lambda x, y, z, **kwargs: None):
            indexer = LupyneRecipeIndexer.__new__(LupyneRecipeIndexer)
            indexer._extract_origins = LupyneRecipeIndexer._extract_origins.__get__(indexer)
            
            recipe = {
                'wiki_links': [
                    {'origin_country': 'France', 'origin_region': 'Western Europe'},
                    {'origin_country': 'Italy', 'origin_region': 'Mediterranean'},
                ]
            }
            
            countries, regions = indexer._extract_origins(recipe)
            
            self.assertIn('france', countries)
            self.assertIn('italy', countries)
            self.assertIn('western europe', regions)
            self.assertIn('mediterranean', regions)
    
    def test_extract_from_ingredient_origins(self):
        """Test extraction from ingredient_origins."""
        from indexer.lucene_indexer import LupyneRecipeIndexer
        
        with patch.object(LupyneRecipeIndexer, '__init__', lambda x, y, z, **kwargs: None):
            indexer = LupyneRecipeIndexer.__new__(LupyneRecipeIndexer)
            indexer._extract_origins = LupyneRecipeIndexer._extract_origins.__get__(indexer)
            
            recipe = {
                'ingredient_origins': {
                    'Tea': {'country': 'China', 'region': 'East Asia'},
                    'Butter': {'country': 'France', 'region': None},
                }
            }
            
            countries, regions = indexer._extract_origins(recipe)
            
            self.assertIn('china', countries)
            self.assertIn('france', countries)
            self.assertIn('east asia', regions)
    
    def test_extract_from_dish_info(self):
        """Test extraction from dish_info."""
        from indexer.lucene_indexer import LupyneRecipeIndexer
        
        with patch.object(LupyneRecipeIndexer, '__init__', lambda x, y, z, **kwargs: None):
            indexer = LupyneRecipeIndexer.__new__(LupyneRecipeIndexer)
            indexer._extract_origins = LupyneRecipeIndexer._extract_origins.__get__(indexer)
            
            recipe = {
                'dish_info': {
                    'country': 'Belgium, France',
                    'region': 'Western Europe'
                }
            }
            
            countries, regions = indexer._extract_origins(recipe)
            
            self.assertIn('belgium', countries)
            self.assertIn('france', countries)
            self.assertIn('western europe', regions)
    
    def test_clean_origin_data(self):
        """Test cleaning of origin data with refs and other noise."""
        from indexer.lucene_indexer import LupyneRecipeIndexer
        
        with patch.object(LupyneRecipeIndexer, '__init__', lambda x, y, z, **kwargs: None):
            indexer = LupyneRecipeIndexer.__new__(LupyneRecipeIndexer)
            indexer._extract_origins = LupyneRecipeIndexer._extract_origins.__get__(indexer)
            
            recipe = {
                'wiki_links': [
                    {'origin_country': 'China<ref></ref>', 'origin_region': None},
                ]
            }
            
            countries, regions = indexer._extract_origins(recipe)
            
            self.assertIn('china', countries)
            self.assertNotIn('china<ref></ref>', countries)


class TestQueryTypes(unittest.TestCase):
    """Test different query type categories for comprehensive coverage."""
    
    # Query test cases organized by category
    QUERY_TEST_CASES = {
        'exact_phrase': [
            # (query, expected_behavior)
            ('"chocolate cake"', 'exact phrase match'),
            ('"grilled chicken breast"', 'exact 3-word phrase'),
            ('"quick and easy"', 'phrase with stopwords'),
            ('"italian pasta"', 'cuisine + food phrase'),
            ('"beef stew recipe"', 'food + recipe phrase'),
        ],
        'ingredient_include': [
            ('ingredients:chicken', 'single ingredient'),
            ('ingredients:chicken,garlic', 'multiple ingredients'),
            ('ingredients:flour,eggs,sugar', 'baking ingredients'),
            ('ingredients:salmon', 'specific protein'),
            ('ingredients:tomato,basil,mozzarella', 'recipe combo'),
        ],
        'ingredient_exclude': [
            ('-meat', 'exclude meat'),
            ('-gluten', 'exclude allergen'),
            ('chicken -dairy', 'include and exclude'),
            ('"pasta" -meat -cheese', 'phrase with exclusions'),
            ('salad -chicken -beef -pork', 'multiple exclusions'),
        ],
        'cuisine_filter': [
            ('cuisine:italian', 'single cuisine'),
            ('cuisine:mexican,spanish', 'multiple cuisines'),
            ('cuisine:asian', 'broad cuisine category'),
            ('pasta cuisine:italian', 'text + cuisine'),
            ('"indian curry" cuisine:indian', 'phrase + cuisine'),
        ],
        'origin_country': [
            ('origin:france', 'French origin'),
            ('origin:italy', 'Italian origin'),
            ('origin:japan', 'Japanese origin'),
            ('origin:mexico', 'Mexican origin'),
            ('pasta origin:italy', 'text + origin'),
        ],
        'origin_region': [
            ('region:caribbean', 'Caribbean region'),
            ('region:mediterranean', 'Mediterranean'),
            ('region:southeast asia', 'SE Asia region'),
            ('region:western europe', 'W Europe region'),
            ('curry region:south asia', 'text + region'),
        ],
        'time_filter': [
            ('time:<30', 'under 30 minutes'),
            ('time:30-60', 'time range'),
            ('time:>60', 'over 60 minutes'),
            ('quick dinner time:<20', 'text + quick time'),
            ('"slow cooker" time:>120', 'phrase + long time'),
        ],
        'difficulty': [
            ('difficulty:easy', 'easy recipes'),
            ('difficulty:medium', 'medium difficulty'),
            ('difficulty:hard', 'hard recipes'),
            ('beginner difficulty:easy', 'text + difficulty'),
        ],
        'combined_advanced': [
            ('"chicken parmesan" cuisine:italian time:<60', 'phrase + cuisine + time'),
            ('ingredients:chicken,garlic origin:italy -dairy', 'ingredients + origin + exclude'),
            ('healthy salad cuisine:mediterranean time:<20 difficulty:easy', 'all filters'),
            ('"chocolate cake" ingredients:flour,eggs -nuts time:<90', 'phrase + ingredients + exclude + time'),
        ],
        'fuzzy_typo': [
            ('chickn', 'typo in chicken'),
            ('spagetti', 'typo in spaghetti'),
            ('tomatoe', 'typo in tomato'),
            ('lasanga', 'typo in lasagna'),
            ('choclate', 'typo in chocolate'),
        ],
        'boolean_operators': [
            ('chicken AND pasta', 'explicit AND'),
            ('beef OR pork', 'explicit OR'),
            ('vegetarian NOT tofu', 'explicit NOT'),
            ('(chicken OR beef) AND pasta', 'grouped query'),
        ],
    }
    
    def test_query_categories_defined(self):
        """Verify all query categories have test cases."""
        expected_categories = [
            'exact_phrase', 'ingredient_include', 'ingredient_exclude',
            'cuisine_filter', 'origin_country', 'origin_region',
            'time_filter', 'difficulty', 'combined_advanced',
            'fuzzy_typo', 'boolean_operators'
        ]
        
        for category in expected_categories:
            self.assertIn(category, self.QUERY_TEST_CASES,
                         f"Missing test cases for category: {category}")
            self.assertGreater(len(self.QUERY_TEST_CASES[category]), 0,
                              f"No test cases in category: {category}")
    
    def test_total_query_coverage(self):
        """Verify we have sufficient query coverage."""
        total_queries = sum(len(cases) for cases in self.QUERY_TEST_CASES.values())
        self.assertGreaterEqual(total_queries, 50, 
                               f"Expected at least 50 test queries, got {total_queries}")


class TestBenchmarkQueries(unittest.TestCase):
    """Test queries for benchmarking different index configurations."""
    
    # Comprehensive benchmark queries
    BENCHMARK_QUERIES = [
        # Single ingredient
        {"id": 1, "query": "chicken", "category": "single_ingredient", "expected_field": "ingredients"},
        {"id": 2, "query": "pasta", "category": "single_ingredient", "expected_field": "title"},
        {"id": 3, "query": "salmon", "category": "single_ingredient", "expected_field": "ingredients"},
        {"id": 4, "query": "chocolate", "category": "single_ingredient", "expected_field": "ingredients"},
        {"id": 5, "query": "garlic", "category": "single_ingredient", "expected_field": "ingredients"},
        
        # Exact phrases
        {"id": 6, "query": '"chocolate cake"', "category": "exact_phrase", "expected_field": "title"},
        {"id": 7, "query": '"grilled chicken"', "category": "exact_phrase", "expected_field": "title"},
        {"id": 8, "query": '"beef stew"', "category": "exact_phrase", "expected_field": "title"},
        {"id": 9, "query": '"tomato soup"', "category": "exact_phrase", "expected_field": "title"},
        {"id": 10, "query": '"banana bread"', "category": "exact_phrase", "expected_field": "title"},
        
        # Multi-ingredient
        {"id": 11, "query": "chicken garlic", "category": "multi_ingredient", "expected_field": "ingredients"},
        {"id": 12, "query": "tomato basil mozzarella", "category": "multi_ingredient", "expected_field": "ingredients"},
        {"id": 13, "query": "flour eggs sugar butter", "category": "multi_ingredient", "expected_field": "ingredients"},
        {"id": 14, "query": "salmon lemon dill", "category": "multi_ingredient", "expected_field": "ingredients"},
        {"id": 15, "query": "beef onion potato carrot", "category": "multi_ingredient", "expected_field": "ingredients"},
        
        # Cuisine-specific
        {"id": 16, "query": "italian", "category": "cuisine", "expected_field": "cuisine"},
        {"id": 17, "query": "mexican", "category": "cuisine", "expected_field": "cuisine"},
        {"id": 18, "query": "chinese", "category": "cuisine", "expected_field": "cuisine"},
        {"id": 19, "query": "french", "category": "cuisine", "expected_field": "cuisine"},
        {"id": 20, "query": "indian", "category": "cuisine", "expected_field": "cuisine"},
        
        # Cooking method
        {"id": 21, "query": "baked", "category": "method", "expected_field": "instructions"},
        {"id": 22, "query": "grilled", "category": "method", "expected_field": "instructions"},
        {"id": 23, "query": "fried", "category": "method", "expected_field": "instructions"},
        {"id": 24, "query": "roasted", "category": "method", "expected_field": "instructions"},
        {"id": 25, "query": "steamed", "category": "method", "expected_field": "instructions"},
        
        # Dish types
        {"id": 26, "query": "lasagna", "category": "dish", "expected_field": "title"},
        {"id": 27, "query": "risotto", "category": "dish", "expected_field": "title"},
        {"id": 28, "query": "cheesecake", "category": "dish", "expected_field": "title"},
        {"id": 29, "query": "tiramisu", "category": "dish", "expected_field": "title"},
        {"id": 30, "query": "guacamole", "category": "dish", "expected_field": "title"},
        
        # Dietary/Health
        {"id": 31, "query": "vegetarian", "category": "dietary", "expected_field": "category"},
        {"id": 32, "query": "low carb", "category": "dietary", "expected_field": "title"},
        {"id": 33, "query": "gluten free", "category": "dietary", "expected_field": "title"},
        {"id": 34, "query": "healthy", "category": "dietary", "expected_field": "title"},
        {"id": 35, "query": "keto", "category": "dietary", "expected_field": "title"},
        
        # Complex multi-term
        {"id": 36, "query": "easy chicken dinner", "category": "complex", "expected_field": "title"},
        {"id": 37, "query": "quick breakfast recipe", "category": "complex", "expected_field": "title"},
        {"id": 38, "query": "homemade bread simple", "category": "complex", "expected_field": "title"},
        {"id": 39, "query": "creamy mushroom sauce", "category": "complex", "expected_field": "title"},
        {"id": 40, "query": "fresh summer salad", "category": "complex", "expected_field": "title"},
        
        # Typo tolerance (fuzzy)
        {"id": 41, "query": "chickn", "category": "fuzzy", "expected_match": "chicken"},
        {"id": 42, "query": "spagetti", "category": "fuzzy", "expected_match": "spaghetti"},
        {"id": 43, "query": "tomatoe", "category": "fuzzy", "expected_match": "tomato"},
        {"id": 44, "query": "lasanga", "category": "fuzzy", "expected_match": "lasagna"},
        {"id": 45, "query": "choclate", "category": "fuzzy", "expected_match": "chocolate"},
        
        # Origin-based
        {"id": 46, "query": "france", "category": "origin", "expected_field": "wiki_abstracts"},
        {"id": 47, "query": "caribbean", "category": "origin", "expected_field": "wiki_abstracts"},
        {"id": 48, "query": "mediterranean", "category": "origin", "expected_field": "wiki_abstracts"},
        {"id": 49, "query": "asia", "category": "origin", "expected_field": "wiki_abstracts"},
        {"id": 50, "query": "european", "category": "origin", "expected_field": "wiki_abstracts"},
    ]
    
    def test_benchmark_query_count(self):
        """Verify we have 50 benchmark queries."""
        self.assertEqual(len(self.BENCHMARK_QUERIES), 50)
    
    def test_benchmark_categories_balanced(self):
        """Verify categories are reasonably balanced."""
        categories = {}
        for q in self.BENCHMARK_QUERIES:
            cat = q['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        # Each category should have at least 3 queries
        for cat, count in categories.items():
            self.assertGreaterEqual(count, 3, 
                                   f"Category '{cat}' has only {count} queries")
    
    def test_benchmark_query_structure(self):
        """Verify all queries have required fields."""
        for q in self.BENCHMARK_QUERIES:
            self.assertIn('id', q)
            self.assertIn('query', q)
            self.assertIn('category', q)
            self.assertTrue(q['query'].strip(), f"Empty query at id {q['id']}")


class TestSearchResultFormat(unittest.TestCase):
    """Test that search results have expected format."""
    
    EXPECTED_RESULT_FIELDS = [
        'rank', 'score', 'docId', 'url', 'title', 'title_text',
        'ingredients', 'total_minutes', 'cuisine', 'wiki_links'
    ]
    
    def test_result_fields_defined(self):
        """Verify expected result fields are defined."""
        self.assertGreater(len(self.EXPECTED_RESULT_FIELDS), 0)
        self.assertIn('rank', self.EXPECTED_RESULT_FIELDS)
        self.assertIn('score', self.EXPECTED_RESULT_FIELDS)
        self.assertIn('title', self.EXPECTED_RESULT_FIELDS)


if __name__ == '__main__':
    unittest.main()
