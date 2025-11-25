"""
HTML fallback parser for extracting recipe data when JSON-LD is not available.
Uses heuristics and HTML structure analysis via Regular Expressions.
"""

import logging
import re
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class HTMLParser:
    """Fallback HTML parser using heuristics and structure analysis via Regex."""
    
    def __init__(self):
        # Pre-compile patterns for performance
        
        # Title: <h1 ...>Title</h1> or <title>Title</title>
        self.title_patterns = [
            re.compile(r'<h1[^>]*>(.*?)</h1>', re.IGNORECASE | re.DOTALL),
            re.compile(r'<title>(.*?)</title>', re.IGNORECASE | re.DOTALL),
            re.compile(r'["\']name["\']\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE)
        ]
        
        # Ingredients: Look for list items or JSON-LD
        self.ingredient_patterns = [
            re.compile(r'<li[^>]*class="[^"]*ingredient[^"]*"[^>]*>(.*?)</li>', re.IGNORECASE | re.DOTALL),
            re.compile(r'ingredients?.*?<ul>(.*?)</ul>', re.IGNORECASE | re.DOTALL)
        ]
        
        # Instructions: Look for list items
        self.instruction_patterns = [
            re.compile(r'<li[^>]*class="[^"]*instruction[^"]*"[^>]*>(.*?)</li>', re.IGNORECASE | re.DOTALL),
            re.compile(r'<li[^>]*class="[^"]*direction[^"]*"[^>]*>(.*?)</li>', re.IGNORECASE | re.DOTALL),
            re.compile(r'<li[^>]*class="[^"]*step[^"]*"[^>]*>(.*?)</li>', re.IGNORECASE | re.DOTALL)
        ]
        
        # Times (Prep, Cook, Total)
        self.time_patterns = {
            'prep': re.compile(r'prep(?:aration)?\s*time[:\s]*PT(\d+H)?(\d+M)?', re.IGNORECASE),
            'cook': re.compile(r'cook\s*time[:\s]*PT(\d+H)?(\d+M)?', re.IGNORECASE),
            'total': re.compile(r'total\s*time[:\s]*PT(\d+H)?(\d+M)?', re.IGNORECASE)
        }
        
        # Fallback time patterns (text based)
        self.text_time_patterns = [
            r'(\d+)\s*(?:hour|hr|h)\s*(?:and\s*)?(\d+)?\s*(?:minute|min|m)?',
            r'(\d+)\s*(?:minute|min|m)',
            r'(\d+)\s*(?:hour|hr|h)',
            r'ready\s*in\s*(\d+)\s*(?:minute|min|m|hour|hr|h)',
            r'prep\s*time[:\s]*(\d+)\s*(?:minute|min|m|hour|hr|h)',
            r'cook\s*time[:\s]*(\d+)\s*(?:minute|min|m|hour|hr|h)',
            r'total\s*time[:\s]*(\d+)\s*(?:minute|min|m|hour|hr|h)'
        ]
        
        # Yield/Servings
        self.yield_pattern = re.compile(r'["\']recipeYield["\']\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE)
        self.yield_text_pattern = re.compile(r'(?:yields?|makes?|serves?)\s*:?\s*(\d+(?:\s*-\s*\d+)?\s*(?:servings?|people)?)', re.IGNORECASE)
        
        # Cuisine
        self.cuisine_pattern = re.compile(r'["\']recipeCuisine["\']\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE)
        
        # Category
        self.category_pattern = re.compile(r'["\']recipeCategory["\']\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE)

    def parse_recipe(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse recipe from HTML content using heuristics."""
        try:
            recipe = {
                'id': self._extract_doc_id(url),
                'url': url,
                'title': self._extract_title(html_content),
                'description': self._extract_description(html_content),
                'ingredients': self._extract_ingredients(html_content),
                'instructions': self._extract_instructions(html_content),
                'times': self._extract_times(html_content),
                'cuisine': self._extract_simple_field(html_content, self.cuisine_pattern),
                'category': self._extract_simple_field(html_content, self.category_pattern),
                'yield': self._extract_yield(html_content),
                'author': self._extract_author(html_content),
                'nutrition': self._extract_nutrition(html_content),
                'ratings': self._extract_ratings(html_content),
                # Default empty fields for compatibility
                'tools': [],
                'keywords': [],
                'image': '',
                'all_images': [],
                'difficulty': '',
                'serving_size': '',
                'author_bio': '',
                'author_location': '',
                'author_stats': {},
                'date_published': ''
            }
            
            logger.debug(f"Successfully parsed recipe using HTML heuristics: {recipe['title']}")
            return recipe
            
        except Exception as e:
            logger.error(f"Error parsing recipe from HTML: {e}")
            return self._create_empty_recipe(url)

    def _extract_doc_id(self, url: str) -> str:
        match = re.search(r'-(\d+)$', url)
        if match:
            return match.group(1)
        match = re.search(r'/(\d+)$', url)
        if match:
            return match.group(1)
        return ""

    def _extract_title(self, html: str) -> str:
        for pattern in self.title_patterns:
            match = pattern.search(html)
            if match:
                return self._clean_text(match.group(1))
        return ""

    def _extract_ingredients(self, html: str) -> List[str]:
        ingredients = []
        # Find all matches for the list item pattern
        matches = self.ingredient_patterns[0].findall(html)
        if matches:
            return [self._clean_text(m) for m in matches]
            
        # Fallback: look for generic list
        match = self.ingredient_patterns[1].search(html)
        if match:
            list_content = match.group(1)
            items = re.findall(r'<li[^>]*>(.*?)</li>', list_content, re.IGNORECASE | re.DOTALL)
            if items:
                return [self._clean_text(i) for i in items]
        return []

    def _extract_instructions(self, html: str) -> List[str]:
        for pattern in self.instruction_patterns:
            matches = pattern.findall(html)
            if matches:
                return [self._clean_text(m) for m in matches]
        return []

    def _extract_times(self, html: str) -> Dict[str, int]:
        times = {'prep': 0, 'cook': 0, 'total': 0}
        
        # Try ISO patterns first
        for key, pattern in self.time_patterns.items():
            match = pattern.search(html)
            if match:
                hours = int(match.group(1)[:-1]) if match.group(1) else 0
                minutes = int(match.group(2)[:-1]) if match.group(2) else 0
                times[key] = hours * 60 + minutes
        
        # Fallback to text patterns
        if not any(times.values()):
            time_text = html.lower() # Naive, but might work for simple pages
            # Ideally we'd limit this to a "times" section
            for pattern in self.text_time_patterns:
                matches = re.finditer(pattern, time_text, re.IGNORECASE)
                for match in matches:
                    val = self._parse_time_match(match)
                    if 'prep' in match.group(0):
                        times['prep'] = val
                    elif 'cook' in match.group(0):
                        times['cook'] = val
                    elif 'total' in match.group(0) or 'ready' in match.group(0):
                        times['total'] = val

        if not times['total'] and (times['prep'] or times['cook']):
            times['total'] = (times['prep'] or 0) + (times['cook'] or 0)
        
        return times

    def _parse_time_match(self, match) -> int:
        try:
            hours = int(match.group(1)) if match.group(1) else 0
            minutes = int(match.group(2)) if match.group(2) else 0
            if 'hour' in match.group(0) or 'hr' in match.group(0) or 'h' in match.group(0):
                return hours * 60 + minutes
            else:
                return hours + minutes
        except (ValueError, IndexError):
            return 0

    def _extract_simple_field(self, html: str, pattern: re.Pattern) -> str:
        match = pattern.search(html)
        if match:
            return self._clean_text(match.group(1))
        return ""
    
    def _extract_yield(self, html: str) -> str:
        # Try JSON-LD style first
        val = self._extract_simple_field(html, self.yield_pattern)
        if val: return val
        
        # Try text pattern
        match = self.yield_text_pattern.search(html)
        if match:
            return self._clean_text(match.group(1))
        return ""

    def _extract_description(self, html: str) -> str:
        match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
        if match:
            return self._clean_text(match.group(1))
        return ""

    def _extract_author(self, html: str) -> str:
        match = re.search(r'submitted\s+by\s+([^<,\n]+)', html, re.IGNORECASE)
        if match:
            return self._clean_text(match.group(1))
        return ""

    def _extract_nutrition(self, html: str) -> Optional[Dict[str, Any]]:
        # Basic regex for nutrition table
        nutrition = {}
        # Look for table rows with nutrition data
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
        for row in rows:
            cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
            if len(cols) >= 2:
                key = self._clean_text(cols[0]).lower()
                val = self._clean_text(cols[1])
                if 'calor' in key: nutrition['calories'] = val
                elif 'fat' in key: nutrition['fat'] = val
                elif 'protein' in key: nutrition['protein'] = val
                elif 'carb' in key: nutrition['carbohydrates'] = val
        return nutrition if nutrition else None

    def _extract_ratings(self, html: str) -> Optional[Dict[str, Any]]:
        ratings = {}
        # Look for rating value
        match = re.search(r'["\']ratingValue["\']\s*:\s*["\']?(\d+(?:\.\d+)?)["\']?', html)
        if match:
            ratings['rating'] = float(match.group(1))
        
        match = re.search(r'["\']reviewCount["\']\s*:\s*["\']?(\d+)["\']?', html)
        if match:
            ratings['review_count'] = int(match.group(1))
            
        return ratings if ratings else None

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
        return re.sub(r'\s+', ' ', text).strip()

    def _create_empty_recipe(self, url: str) -> Dict[str, Any]:
        return {
            'id': self._extract_doc_id(url),
            'url': url,
            'title': '',
            'description': '',
            'ingredients': [],
            'instructions': [],
            'times': {'prep': 0, 'cook': 0, 'total': 0},
            'cuisine': [],
            'category': [],
            'tools': [],
            'yield': '',
            'author': '',
            'author_bio': '',
            'author_location': '',
            'author_stats': {},
            'keywords': [],
            'date_published': '',
            'image': '',
            'all_images': [],
            'difficulty': '',
            'serving_size': '',
            'nutrition': None,
            'ratings': None
        }
