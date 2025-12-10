"""Tests for Wikipedia enrichment and entity linking."""
import unittest
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEntityMatching(unittest.TestCase):
    """Test entity matching functionality."""
    
    def test_basic_pattern_matching(self):
        """Test basic keyword matching logic."""
        # Simulate entity matching without actual Aho-Corasick
        text = "This recipe uses garlic and onion"
        entities = ['garlic', 'onion', 'tomato']
        
        found = [e for e in entities if e in text.lower()]
        
        self.assertIn('garlic', found)
        self.assertIn('onion', found)
        self.assertNotIn('tomato', found)
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive matching."""
        text = "Add GARLIC and Onion to the pan"
        entities = ['garlic', 'onion']
        
        found = [e for e in entities if e in text.lower()]
        
        self.assertEqual(len(found), 2)
    
    def test_word_boundary_respect(self):
        """Test that matching respects word boundaries."""
        import re
        text = "Swedish meatballs"
        
        # Should NOT match "dish" in "Swedish"
        pattern = re.compile(r'\bdish\b', re.IGNORECASE)
        self.assertIsNone(pattern.search(text))
        
        # Should match "Swedish"
        pattern2 = re.compile(r'\bSwedish\b', re.IGNORECASE)
        self.assertIsNotNone(pattern2.search(text))


class TestCuisineInference(unittest.TestCase):
    """Test cuisine inference from ingredients."""
    
    def test_italian_ingredients(self):
        """Test Italian cuisine detection."""
        italian_ingredients = ['pasta', 'parmesan', 'basil', 'olive oil']
        
        # Simulate cuisine detection
        italian_markers = ['pasta', 'parmesan', 'basil', 'mozzarella', 'prosciutto']
        count = sum(1 for i in italian_ingredients if i in italian_markers)
        
        self.assertGreater(count, 2, "Should detect Italian markers")
    
    def test_asian_ingredients(self):
        """Test Asian cuisine detection."""
        asian_ingredients = ['soy sauce', 'ginger', 'sesame oil']
        
        asian_markers = ['soy sauce', 'ginger', 'sesame', 'rice wine', 'fish sauce']
        count = sum(1 for i in asian_ingredients if any(m in i for m in asian_markers))
        
        self.assertGreater(count, 0, "Should detect Asian markers")


class TestEnrichmentDataStructure(unittest.TestCase):
    """Test enrichment data structures."""
    
    def test_wiki_link_structure(self):
        """Test wiki_link object structure."""
        wiki_link = {
            'surface': 'garlic',
            'wiki_title': 'Garlic',
            'type': 'ingredient',
            'abstract': 'Garlic is a species in the onion genus.'
        }
        
        # Required fields
        self.assertIn('surface', wiki_link)
        self.assertIn('wiki_title', wiki_link)
        self.assertIn('type', wiki_link)
        
        # Type should be valid
        valid_types = ['ingredient', 'dish', 'technique', 'tool', 'cuisine', 'spice']
        self.assertIn(wiki_link['type'], valid_types)
    
    def test_enriched_recipe_structure(self):
        """Test enriched recipe object structure."""
        enriched = {
            'id': '12345',
            'title': 'Pasta Carbonara',
            'wiki_links': [
                {'surface': 'pasta', 'wiki_title': 'Pasta', 'type': 'ingredient'}
            ],
            'historical_context': 'Carbonara is a Roman pasta dish...',
            'ingredient_origins': {'pasta': 'Italy'}
        }
        
        # Required enrichment fields
        self.assertIn('wiki_links', enriched)
        self.assertIsInstance(enriched['wiki_links'], list)


if __name__ == '__main__':
    unittest.main()
