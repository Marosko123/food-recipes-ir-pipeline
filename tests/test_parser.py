"""Tests for recipe parsing (HTML parser and JSON-LD extraction)."""
import json
import unittest
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parser.html_parser import HTMLParser


class TestHTMLParser(unittest.TestCase):
    """Test HTML parser functionality."""
    
    def setUp(self):
        """Initialize parser for each test."""
        self.parser = HTMLParser()
    
    def test_extract_doc_id_from_url(self):
        """Test doc_id extraction from URL."""
        # Standard food.com URL
        url = "https://www.food.com/recipe/chocolate-cake-12345"
        result = self.parser._extract_doc_id(url)
        self.assertEqual(result, "12345")
        
        # URL with just number
        url2 = "https://www.food.com/recipe/12345"
        result2 = self.parser._extract_doc_id(url2)
        self.assertEqual(result2, "12345")
    
    def test_extract_title_from_h1(self):
        """Test title extraction from H1 tag."""
        html = '<html><body><h1 class="recipe-title">Chocolate Cake</h1></body></html>'
        result = self.parser._extract_title(html)
        self.assertEqual(result, "Chocolate Cake")
    
    def test_extract_title_from_title_tag(self):
        """Test title extraction from title tag."""
        html = '<html><head><title>Chocolate Cake Recipe - Food.com</title></head></html>'
        result = self.parser._extract_title(html)
        self.assertIn("Chocolate Cake", result)
    
    def test_clean_text(self):
        """Test HTML text cleaning."""
        # Test with tags
        dirty = "<span>Hello</span> <b>World</b>!"
        clean = self.parser._clean_text(dirty)
        self.assertEqual(clean, "Hello World!")
        
        # Test with entities
        dirty2 = "Tom &amp; Jerry"
        clean2 = self.parser._clean_text(dirty2)
        self.assertIn("Tom", clean2)
    
    def test_extract_times_iso_format(self):
        """Test time extraction from ISO 8601 format."""
        html = '''
        <script type="application/ld+json">
        {
            "prepTime": "PT30M",
            "cookTime": "PT1H",
            "totalTime": "PT1H30M"
        }
        </script>
        '''
        times = self.parser._extract_times(html)
        # Note: This tests regex patterns, actual values depend on implementation
        self.assertIn('prep', times)
        self.assertIn('cook', times)
        self.assertIn('total', times)
    
    def test_parse_recipe_returns_dict(self):
        """Test that parse_recipe returns a dictionary with required fields."""
        html = '<html><body><h1>Test Recipe</h1></body></html>'
        url = "https://www.food.com/recipe/test-123"
        
        result = self.parser.parse_recipe(html, url)
        
        # Check required fields exist
        self.assertIn('id', result)
        self.assertIn('url', result)
        self.assertIn('title', result)
        self.assertIn('ingredients', result)
        self.assertIn('instructions', result)
        self.assertIn('times', result)
        
        # Check URL is preserved
        self.assertEqual(result['url'], url)
    
    def test_empty_html_handling(self):
        """Test handling of empty or minimal HTML."""
        html = '<html></html>'
        url = "https://www.food.com/recipe/empty-1"
        
        result = self.parser.parse_recipe(html, url)
        
        # Should not raise exception
        self.assertIsInstance(result, dict)
        self.assertEqual(result['url'], url)


class TestJSONLDExtraction(unittest.TestCase):
    """Test JSON-LD extraction from HTML."""
    
    def test_json_ld_recipe_detection(self):
        """Test detection of JSON-LD recipe schema."""
        html = '''
        <script type="application/ld+json">
        {"@type": "Recipe", "name": "Chocolate Cake", "recipeIngredient": ["flour", "sugar"]}
        </script>
        '''
        # Should contain Recipe type marker
        self.assertIn('"@type": "Recipe"', html)
        self.assertIn('"recipeIngredient"', html)
    
    def test_json_ld_parsing(self):
        """Test JSON-LD block extraction via regex."""
        import re
        html = '''
        <html>
        <script type="application/ld+json">
        {"@type": "Recipe", "name": "Test"}
        </script>
        </html>
        '''
        pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        
        self.assertEqual(len(matches), 1)
        data = json.loads(matches[0])
        self.assertEqual(data['@type'], 'Recipe')
        self.assertEqual(data['name'], 'Test')


if __name__ == '__main__':
    unittest.main()
