"""
Unit tests for crawler seed extraction functionality.
"""
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import gzip
import xml.etree.ElementTree as ET

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from crawler.robots import parse_robots, is_allowed
from crawler.sitemap import iter_urls_from_sitemap, filter_recipe_urls
from crawler.util import extract_doc_id, canonicalize, sha1_url


class TestRobotsParsing(unittest.TestCase):
    """Test robots.txt parsing functionality."""
    
    def test_parse_robots_basic(self):
        """Test basic robots.txt parsing."""
        robots_text = """
User-agent: *
Disallow: /search/
Disallow: /finder/
Disallow: *.php
Disallow: *.zsp

User-agent: FoodRecipesBot
Disallow: /admin/

Sitemap: https://www.food.com/sitemap.xml
Sitemap: https://www.food.com/sitemap-recipes.xml.gz
"""
        
        result = parse_robots(robots_text)
        
        self.assertIn("disallow", result)
        self.assertIn("sitemaps", result)
        self.assertEqual(len(result["disallow"]), 4)  # All disallow rules
        self.assertEqual(len(result["sitemaps"]), 2)
        self.assertIn("/search/", result["disallow"])
        self.assertIn("https://www.food.com/sitemap.xml", result["sitemaps"])
    
    def test_is_allowed_basic(self):
        """Test URL allowance checking."""
        disallow_patterns = ["/search/", "/finder/", "*.php", "*.zsp"]
        
        # Allowed URLs
        self.assertTrue(is_allowed("https://www.food.com/recipe/chicken-123", disallow_patterns))
        self.assertTrue(is_allowed("https://www.food.com/", disallow_patterns))
        self.assertTrue(is_allowed("https://www.food.com/recipe/pasta-456/", disallow_patterns))
        
        # Disallowed URLs
        self.assertFalse(is_allowed("https://www.food.com/search/", disallow_patterns))
        self.assertFalse(is_allowed("https://www.food.com/finder/", disallow_patterns))
        self.assertFalse(is_allowed("https://www.food.com/page.php", disallow_patterns))
        self.assertFalse(is_allowed("https://www.food.com/script.zsp", disallow_patterns))


class TestSitemapParsing(unittest.TestCase):
    """Test sitemap parsing functionality."""
    
    def test_iter_urls_from_sitemap_xml(self):
        """Test URL extraction from XML sitemap."""
        # Create a mock XML sitemap
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://www.food.com/recipe/chicken-123</loc>
        <lastmod>2023-01-01</lastmod>
    </url>
    <url>
        <loc>https://www.food.com/recipe/pasta-456</loc>
        <lastmod>2023-01-02</lastmod>
    </url>
    <url>
        <loc>https://www.food.com/search/</loc>
        <lastmod>2023-01-03</lastmod>
    </url>
</urlset>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(sitemap_xml)
            temp_file = f.name
        
        try:
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.text = sitemap_xml
                mock_response.headers = {}
                mock_get.return_value = mock_response
                
                urls = list(iter_urls_from_sitemap(f"file://{temp_file}"))
                
                self.assertEqual(len(urls), 3)
                self.assertIn("https://www.food.com/recipe/chicken-123", urls)
                self.assertIn("https://www.food.com/recipe/pasta-456", urls)
                self.assertIn("https://www.food.com/search/", urls)
        
        finally:
            os.unlink(temp_file)
    
    def test_iter_urls_from_sitemap_gz(self):
        """Test URL extraction from gzipped sitemap."""
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://www.food.com/recipe/soup-789</loc>
    </url>
</urlset>"""
        
        # Create gzipped content
        gz_content = gzip.compress(sitemap_xml.encode('utf-8'))
        
        with tempfile.NamedTemporaryFile(suffix='.xml.gz', delete=False) as f:
            f.write(gz_content)
            temp_file = f.name
        
        try:
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.content = gz_content
                mock_response.headers = {'content-encoding': 'gzip'}
                mock_get.return_value = mock_response
                
                urls = list(iter_urls_from_sitemap(f"file://{temp_file}"))
                
                self.assertEqual(len(urls), 1)
                self.assertIn("https://www.food.com/recipe/soup-789", urls)
        
        finally:
            os.unlink(temp_file)
    
    def test_filter_recipe_urls(self):
        """Test recipe URL filtering."""
        urls = [
            "https://www.food.com/recipe/chicken-123",
            "https://www.food.com/recipe/pasta-456/",
            "https://www.food.com/search/",
            "https://www.food.com/recipe/soup-789",
            "https://www.food.com/",
            "https://www.food.com/recipe/dessert-999?ref=home"
        ]
        
        recipe_urls = list(filter_recipe_urls(urls))
        
        self.assertEqual(len(recipe_urls), 4)
        self.assertIn("https://www.food.com/recipe/chicken-123", recipe_urls)
        self.assertIn("https://www.food.com/recipe/pasta-456/", recipe_urls)
        self.assertIn("https://www.food.com/recipe/soup-789", recipe_urls)
        self.assertIn("https://www.food.com/recipe/dessert-999?ref=home", recipe_urls)


class TestUtilFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_extract_doc_id(self):
        """Test document ID extraction from URLs."""
        test_cases = [
            ("https://www.food.com/recipe/chicken-123", "123"),
            ("https://www.food.com/recipe/pasta-456/", "456"),
            ("https://www.food.com/recipe/soup-789?ref=home", "789"),
            ("https://www.food.com/recipe/dessert-999", "999"),
            ("https://www.food.com/search/", None),
            ("https://www.food.com/", None),
        ]
        
        for url, expected_id in test_cases:
            with self.subTest(url=url):
                result = extract_doc_id(url)
                self.assertEqual(result, expected_id)
    
    def test_canonicalize_with_html(self):
        """Test URL canonicalization with HTML."""
        url = "https://www.food.com/recipe/chicken-123?ref=home"
        html = '<html><head><link rel="canonical" href="https://www.food.com/recipe/chicken-123"></head></html>'
        
        canonical = canonicalize(url, html)
        self.assertEqual(canonical, "https://www.food.com/recipe/chicken-123")
    
    def test_canonicalize_without_html(self):
        """Test URL canonicalization without HTML."""
        url = "https://www.food.com/recipe/chicken-123?ref=home"
        
        canonical = canonicalize(url, None)
        self.assertEqual(canonical, url)
    
    def test_sha1_url(self):
        """Test URL hashing for deduplication."""
        url1 = "https://www.food.com/recipe/chicken-123"
        url2 = "https://www.food.com/recipe/chicken-123"
        url3 = "https://www.food.com/recipe/pasta-456"
        
        hash1 = sha1_url(url1)
        hash2 = sha1_url(url2)
        hash3 = sha1_url(url3)
        
        self.assertEqual(hash1, hash2)  # Same URL should have same hash
        self.assertNotEqual(hash1, hash3)  # Different URLs should have different hashes
        self.assertEqual(len(hash1), 40)  # SHA1 hash is 40 characters


class TestIntegration(unittest.TestCase):
    """Integration tests for seed extraction workflow."""
    
    def test_deduplication_workflow(self):
        """Test the complete deduplication workflow."""
        from crawler.util import deduplicate_urls
        
        urls = [
            "https://www.food.com/recipe/chicken-123",
            "https://www.food.com/recipe/pasta-456",
            "https://www.food.com/recipe/chicken-123",  # Duplicate
            "https://www.food.com/recipe/soup-789",
            "https://www.food.com/recipe/pasta-456",  # Duplicate
        ]
        
        unique_urls = list(deduplicate_urls(urls))
        
        self.assertEqual(len(unique_urls), 3)
        self.assertEqual(len(set(unique_urls)), 3)  # All unique


if __name__ == '__main__':
    unittest.main()

